//
// Copyright (c) 2001-2012 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "clipboard.h"

#include <afxole.h>
#include "file_op_thread.h"
#include "bitmap.h"
#include "winapi_ex.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
xpr_bool_t FillFormatEtc(LPFORMATETC aFormatEtc, CLIPFORMAT aClipFormat)
{
    if (XPR_IS_NULL(aFormatEtc) || aClipFormat == 0)
        return XPR_FALSE;

    aFormatEtc->cfFormat = aClipFormat;
    aFormatEtc->ptd      = XPR_NULL;
    aFormatEtc->dwAspect = DVASPECT_CONTENT;
    aFormatEtc->lindex   = -1;
    aFormatEtc->tymed    = (DWORD)-1;

    return XPR_TRUE;
}

void SetClipboard(LPDATAOBJECT aDataObject, DROPEFFECT aDropEffect, CLIPFORMAT *aClipFormat)
{
    if (XPR_IS_NULL(aDataObject))
        return;

    COleDataSource *sDataSource = new COleDataSource;
    if (XPR_IS_NULL(sDataSource))
        return;

    STGMEDIUM sStgMedium = {0};
    FORMATETC sFormatEtc = {0};

    sFormatEtc.ptd      = (DVTARGETDEVICE FAR *)XPR_NULL;
    sFormatEtc.dwAspect = DVASPECT_CONTENT;
    sFormatEtc.lindex   = -1;
    sFormatEtc.tymed    = TYMED_HGLOBAL;

    // ShellIDList
    sFormatEtc.cfFormat = aClipFormat[0];
    aDataObject->GetData(&sFormatEtc, &sStgMedium);
    sDataSource->CacheGlobalData(aClipFormat[0], sStgMedium.hGlobal);

    // Unknown Clipformat - HDROP
    memset(&sStgMedium, 0, sizeof(STGMEDIUM));
    sFormatEtc.cfFormat = CF_HDROP;
    aDataObject->GetData(&sFormatEtc, &sStgMedium);
    sDataSource->CacheGlobalData(CF_HDROP, sStgMedium.hGlobal);

    // DropEffect
    HGLOBAL sGlobal = ::GlobalAlloc(GHND | GMEM_SHARE, sizeof(DROPEFFECT));
    DROPEFFECT *sDropEffect = (DROPEFFECT *)::GlobalLock(sGlobal);
    *sDropEffect = aDropEffect;
    ::GlobalUnlock(sGlobal);
    sDataSource->CacheGlobalData(aClipFormat[1], sGlobal);

    // FileName
    memset(&sStgMedium, 0, sizeof(STGMEDIUM));
    sFormatEtc.cfFormat = aClipFormat[2];
    aDataObject->GetData(&sFormatEtc, &sStgMedium);
    sDataSource->CacheGlobalData(aClipFormat[2], sStgMedium.hGlobal);

    // FileNameW
    memset(&sStgMedium, 0, sizeof(STGMEDIUM));
    sFormatEtc.cfFormat = aClipFormat[3];
    aDataObject->GetData(&sFormatEtc, &sStgMedium);
    sDataSource->CacheGlobalData(aClipFormat[3], sStgMedium.hGlobal);

    sDataSource->SetClipboard();
}

xpr_bool_t DoPaste(HWND               aHwnd,
                   CLIPFORMAT         aShellIDListClipFormat,
                   CLIPFORMAT         aDropEffectClipFormat,
                   const xpr_tchar_t *aTarget,
                   const xpr_tchar_t *aLinkSuffix,
                   xpr_uint_t         aMsg,
                   xpr_bool_t         aCopy)
{
    COleDataObject sOleDataObject;
    if (sOleDataObject.AttachClipboard() == XPR_FALSE)
        return XPR_FALSE;

    DROPEFFECT sDropEffect = aDropEffectClipFormat;
    if (aDropEffectClipFormat > 4)
    {
        HGLOBAL sGlobal = sOleDataObject.GetGlobalData(aDropEffectClipFormat);
        if (XPR_IS_NULL(sGlobal))
            return XPR_FALSE;

        sDropEffect = *((DROPEFFECT *)::GlobalLock(sGlobal));

        ::GlobalUnlock(sGlobal);
    }

    return DoPaste(aHwnd, &sOleDataObject, XPR_FALSE, aShellIDListClipFormat, sDropEffect, aTarget, aLinkSuffix, aMsg, aCopy);
}

xpr_bool_t DoPaste(HWND               aHwnd,
                   COleDataObject    *aOleDataObject,
                   xpr_bool_t         aDragDrop,
                   CLIPFORMAT         aShellIDListClipFormat,
                   DROPEFFECT         aDropEffect,
                   const xpr_tchar_t *aTarget,
                   const xpr_tchar_t *aLinkSuffix,
                   xpr_uint_t         aMsg,
                   xpr_bool_t         aCopy)
{
    if (XPR_IS_NULL(aOleDataObject) ||
        XPR_IS_NULL(aTarget) ||
        aTarget[0] == XPR_STRING_LITERAL('\0'))
    {
        return XPR_FALSE;
    }

    xpr_bool_t sResult = XPR_FALSE;

    CWaitCursor sWaitCursor;
    if (aOleDataObject->IsDataAvailable(aShellIDListClipFormat) == XPR_TRUE &&
        aDropEffect == DROPEFFECT_LINK)
    {
        STGMEDIUM sStgMedium = {0};
        FORMATETC sFormatEtc =
            {aShellIDListClipFormat, XPR_NULL, DVASPECT_CONTENT, -1, TYMED_HGLOBAL};

        if (aOleDataObject->GetData(
                aShellIDListClipFormat,
                &sStgMedium,
                &sFormatEtc) == XPR_TRUE)
        {
            LPIDA sIda =
                (LPIDA)::GlobalLock(sStgMedium.hGlobal);

            if (XPR_IS_NOT_NULL(sIda))
            {
                const xpr_sint_t sCount = sIda->cidl;

                xpr_tchar_t *sMultipleSource = XPR_NULL;
                xpr_tchar_t *sMultipleSourceEnum = XPR_NULL;
                if (XPR_IS_NOT_NULL(aHwnd) && aMsg >= WM_USER)
                {
                    sMultipleSource =
                        new xpr_tchar_t[
                            (XPR_MAX_PATH + 1) * sCount + 1];
                    sMultipleSourceEnum = sMultipleSource;
                }

                LPSHELLFOLDER sDesktopShellFolder = XPR_NULL;
                HRESULT sHResult =
                    ::SHGetDesktopFolder(&sDesktopShellFolder);

                LPSHELLFOLDER sShellFolder = XPR_NULL;
                if (SUCCEEDED(sHResult) &&
                    XPR_IS_NOT_NULL(sDesktopShellFolder))
                {
                    LPITEMIDLIST sFolderPidl =
                        (LPITEMIDLIST)(
                            (xpr_byte_t *)sIda +
                            sIda->aoffset[0]);

                    sHResult =
                        sDesktopShellFolder->BindToObject(
                            sFolderPidl,
                            XPR_NULL,
                            IID_IShellFolder,
                            (LPVOID *)&sShellFolder);
                    if (FAILED(sHResult) ||
                        XPR_IS_NULL(sShellFolder))
                    {
                        sShellFolder = sDesktopShellFolder;
                        sDesktopShellFolder = XPR_NULL;
                    }

                    xpr::string sLinkSuffix =
                        XPR_IS_NOT_NULL(aLinkSuffix) ?
                        aLinkSuffix :
                        XPR_STRING_LITERAL(" - Shortcut");

                    for (xpr_sint_t i = 0; i < sCount; ++i)
                    {
                        LPITEMIDLIST sItemPidl =
                            (LPITEMIDLIST)(
                                (xpr_byte_t *)sIda +
                                sIda->aoffset[i + 1]);
                        LPITEMIDLIST sFullPidl =
                            fxfile::base::Pidl::concat(
                                sFolderPidl,
                                sItemPidl);

                        if (XPR_IS_NOT_NULL(sFullPidl))
                        {
                            xpr::string sName;
                            GetName(
                                sShellFolder,
                                sItemPidl,
                                SHGDN_INFOLDER,
                                sName);

                            const xpr_size_t sColon =
                                sName.find(
                                    XPR_STRING_LITERAL(':'));
                            if (sColon != xpr::string::npos)
                                sName.erase(sColon, 1);

                            sName += sLinkSuffix;

                            xpr_tchar_t sLink[
                                XPR_MAX_PATH + 1] = {0};
                            if (SetNewPath(
                                    sLink,
                                    aTarget,
                                    sName.c_str(),
                                    XPR_STRING_LITERAL(".lnk")) == XPR_TRUE &&
                                CreateShortcut(
                                    sLink,
                                    sFullPidl) == XPR_TRUE)
                            {
                                sResult = XPR_TRUE;

                                if (XPR_IS_NOT_NULL(
                                        sMultipleSourceEnum))
                                {
                                    _tcscpy(
                                        sMultipleSourceEnum,
                                        sLink);
                                    sMultipleSourceEnum +=
                                        _tcslen(
                                            sMultipleSourceEnum) +
                                        1;
                                }
                            }
                        }

                        COM_FREE(sFullPidl);
                    }
                }

                if (XPR_IS_NOT_NULL(sMultipleSourceEnum))
                    sMultipleSourceEnum[0] =
                        XPR_STRING_LITERAL('\0');

                if (XPR_IS_TRUE(sResult))
                {
                    ::SHChangeNotify(
                        SHCNE_UPDATEDIR,
                        SHCNF_PATH | SHCNF_FLUSH,
                        (LPCVOID)aTarget,
                        XPR_NULL);

                    if (XPR_IS_NOT_NULL(sMultipleSource) &&
                        XPR_IS_NOT_NULL(aHwnd) &&
                        aMsg >= WM_USER)
                    {
                        PasteSelItems sPasteSelItems = {0};
                        sPasteSelItems.mSource =
                            sMultipleSource;
                        sPasteSelItems.mTarget =
                            aTarget;
                        ::SendMessage(
                            aHwnd,
                            aMsg,
                            (WPARAM)&sPasteSelItems,
                            0);
                    }
                }

                XPR_SAFE_DELETE_ARRAY(sMultipleSource);
                COM_RELEASE(sShellFolder);
                COM_RELEASE(sDesktopShellFolder);
                ::GlobalUnlock(sStgMedium.hGlobal);
            }

            ::ReleaseStgMedium(&sStgMedium);
        }

        return sResult;
    }

    xpr_uint_t sFiles = 0;
    xpr_tchar_t *sMultipleSource = XPR_NULL;
    xpr_tchar_t *sMultipleSourceEnum = XPR_NULL;
    xpr_tchar_t *sTarget = XPR_NULL;

    if (aOleDataObject->IsDataAvailable(aShellIDListClipFormat) == XPR_TRUE)
    {
        STGMEDIUM sStgMedium = {0};
        FORMATETC sFormatEtc =
            {aShellIDListClipFormat, XPR_NULL, DVASPECT_CONTENT, -1, TYMED_HGLOBAL};

        if (aOleDataObject->GetData(
                aShellIDListClipFormat,
                &sStgMedium,
                &sFormatEtc) == XPR_TRUE)
        {
            LPIDA sIda =
                (LPIDA)::GlobalLock(sStgMedium.hGlobal);
            if (XPR_IS_NOT_NULL(sIda))
            {
                sFiles = sIda->cidl;

                LPSHELLFOLDER sDesktopShellFolder =
                    XPR_NULL;
                HRESULT sHResult =
                    ::SHGetDesktopFolder(
                        &sDesktopShellFolder);

                if (SUCCEEDED(sHResult) &&
                    XPR_IS_NOT_NULL(sDesktopShellFolder) &&
                    sFiles > 0)
                {
                    LPITEMIDLIST sFolderPidl =
                        (LPITEMIDLIST)(
                            (xpr_byte_t *)sIda +
                            sIda->aoffset[0]);

                    LPSHELLFOLDER sShellFolder =
                        XPR_NULL;
                    sHResult =
                        sDesktopShellFolder->BindToObject(
                            sFolderPidl,
                            XPR_NULL,
                            IID_IShellFolder,
                            (LPVOID *)&sShellFolder);
                    if (FAILED(sHResult) ||
                        XPR_IS_NULL(sShellFolder))
                    {
                        sShellFolder =
                            sDesktopShellFolder;
                        sDesktopShellFolder =
                            XPR_NULL;
                    }

                    sMultipleSource =
                        new xpr_tchar_t[
                            (XPR_MAX_PATH + 1) *
                            sFiles +
                            1];
                    memset(
                        sMultipleSource,
                        0,
                        sizeof(xpr_tchar_t) *
                            ((XPR_MAX_PATH + 1) *
                             sFiles +
                             1));
                    sMultipleSourceEnum =
                        sMultipleSource;

                    for (xpr_uint_t i = 0;
                         i < sFiles;
                         ++i)
                    {
                        LPITEMIDLIST sItemPidl =
                            (LPITEMIDLIST)(
                                (xpr_byte_t *)sIda +
                                sIda->aoffset[i + 1]);

                        xpr_tchar_t sPath[
                            XPR_MAX_PATH + 1] = {0};
                        if (SUCCEEDED(
                                GetName(
                                    sShellFolder,
                                    sItemPidl,
                                    SHGDN_FORPARSING,
                                    sPath)))
                        {
                            _tcscpy(
                                sMultipleSourceEnum,
                                sPath);
                            sMultipleSourceEnum +=
                                _tcslen(
                                    sMultipleSourceEnum) +
                                1;
                        }
                    }

                    sMultipleSourceEnum[0] =
                        XPR_STRING_LITERAL('\0');
                    sResult = XPR_TRUE;

                    COM_RELEASE(sShellFolder);
                }

                COM_RELEASE(sDesktopShellFolder);
                ::GlobalUnlock(sStgMedium.hGlobal);
            }

            ::ReleaseStgMedium(&sStgMedium);
        }
    }

    if (XPR_IS_FALSE(sResult) && aOleDataObject->IsDataAvailable(CF_HDROP) == XPR_TRUE)
    {
        // First, Get Global Data(CF_HDROP)
        HDROP sDrop =
            (HDROP)aOleDataObject->GetGlobalData(CF_HDROP);

        if (XPR_IS_NOT_NULL(sDrop))
            sFiles =
                ::DragQueryFile(
                    sDrop,
                    0xFFFFFFFF,
                    XPR_NULL,
                    0); // 0xFFFFFFFF = item count

        if (XPR_IS_NOT_NULL(sDrop) && sFiles > 0)
        {
            xpr_sint_t i;
            xpr_tchar_t sPath[XPR_MAX_PATH + 1];
            sMultipleSource = new xpr_tchar_t[(XPR_MAX_PATH + 1) * sFiles + 1];
            sMultipleSourceEnum = sMultipleSource;

            for (i = 0; i < (xpr_sint_t)sFiles; ++i)
            {
                ::DragQueryFile(sDrop, i, sPath, XPR_MAX_PATH);

                _tcscpy(sMultipleSourceEnum, sPath);

                sMultipleSourceEnum += _tcslen(sMultipleSourceEnum) + 1;
            }

            sMultipleSourceEnum[0] = '\0'; // double end null
        }

        if (XPR_IS_NOT_NULL(sDrop))
        {
            ::GlobalUnlock(sDrop);
            ::DragFinish(sDrop);
        }

        if (sFiles > 0)
            sResult = XPR_TRUE;
    }

    if (XPR_IS_FALSE(sResult))
    {
        XPR_SAFE_DELETE_ARRAY(sMultipleSource);
        XPR_SAFE_DELETE_ARRAY(sTarget);
        return sResult;
    }

    // check target file name (double end null)
    // +---+---+---+---+---+---+---+---+---+---+---+
    // | P | A | T | H | \0| P | A | T | H | \0| \0|
    // +---+---+---+---+---+---+---+---+---+---+---+

    sTarget = new xpr_tchar_t[XPR_MAX_PATH + 1];
    _tcscpy(sTarget, aTarget);

    xpr_sint_t sLen = (xpr_sint_t)_tcslen(sTarget);
    if (sTarget[sLen - 1] == '\\')
        sTarget[sLen - 1] = '\0';
    sLen = (xpr_sint_t)_tcslen(sTarget);
    sTarget[sLen + 1] = '\0';

    xpr_uint_t sFunc = 0;
    WORD sFlags = 0;
    // Drop Effect
    // 1-Copy, 2-Move, 3-Link, 5-Copy+Link
    if (aDropEffect == DROPEFFECT_MOVE)
        sFunc = FO_MOVE;
    else
    {
        sFunc = FO_COPY;

        CString sCompare;
        AfxExtractSubString(sCompare, sMultipleSource, 0, '\0');
        sCompare = sCompare.Left(sCompare.ReverseFind('\\'));
        if (_tcscmp(sCompare, sTarget) == 0)
            sFlags |= FOF_RENAMEONCOLLISION;
    }

    // windows vista bug
    //if (sFiles > 1)
    //  sFlags |= FOF_MULTIDESTFILES;

    if (XPR_IS_TRUE(aCopy))
        sFlags |= FOF_RENAMEONCOLLISION;

    SHFILEOPSTRUCT *pshfo = new SHFILEOPSTRUCT;
    memset(pshfo, 0, sizeof(SHFILEOPSTRUCT));
    pshfo->hwnd   = AfxGetMainWnd()->GetSafeHwnd();
    pshfo->wFunc  = sFunc;
    pshfo->fFlags = sFlags;
    pshfo->pFrom  = sMultipleSource;
    pshfo->pTo    = sTarget;

    if (XPR_IS_FALSE(aDragDrop) && sFunc == FO_MOVE)
    {
        // Empty clipboard - The first parameter of OleSetClipboard function is XPR_NULL
        ::OleSetClipboard(XPR_NULL);
    }

    FileOpThread *sFileOpThread = new FileOpThread;
    sFileOpThread->start(pshfo, aMsg >= WM_USER, aHwnd, aMsg);

    return sResult;
}

xpr_sint_t GetDataObjectFormatCount(COleDataObject *aOleDataObject)
{
    if (XPR_IS_NULL(aOleDataObject))
        return 0;

    xpr_sint_t sFormatCount = 0;

    FORMATETC sFormatEtc = {0};
    aOleDataObject->BeginEnumFormats();
    while (aOleDataObject->GetNextFormat(&sFormatEtc))
        sFormatCount++;

    return sFormatCount;
}

xpr_bool_t DoPasteText(LPDATAOBJECT aDataObject, const xpr_tchar_t *aPath)
{
    if (XPR_IS_NULL(aDataObject) || XPR_IS_NULL(aPath))
        return XPR_FALSE;

    xpr_bool_t sResult = XPR_FALSE;

    FORMATETC sTextFormatEtc =
        { CF_TEXT, XPR_NULL, DVASPECT_CONTENT, -1, TYMED_HGLOBAL };

    STGMEDIUM sStgMedium = {0};
    const HRESULT sComResult =
        aDataObject->GetData(&sTextFormatEtc, &sStgMedium);

    if (SUCCEEDED(sComResult))
    {
        xpr_char_t *sText =
            (xpr_char_t *)::GlobalLock(sStgMedium.hGlobal);
        if (XPR_IS_NOT_NULL(sText))
        {
            const xpr_ssize_t sTextBytes =
                (xpr_ssize_t)strlen(sText);
            xpr_sint_t sOpenMode =
                xpr::FileIo::OpenModeCreate |
                xpr::FileIo::OpenModeTruncate |
                xpr::FileIo::OpenModeWriteOnly;
            xpr::FileIo sFileIo;

            xpr_rcode_t sRcode = sFileIo.open(aPath, sOpenMode);
            if (XPR_RCODE_IS_SUCCESS(sRcode))
            {
                xpr_ssize_t sWritten = 0;
                if (sTextBytes == 0)
                {
                    sResult = XPR_TRUE;
                }
                else
                {
                    sRcode =
                        sFileIo.write(
                            sText,
                            sTextBytes,
                            &sWritten);
                    if (XPR_RCODE_IS_SUCCESS(sRcode) &&
                        sWritten == sTextBytes)
                    {
                        sResult = XPR_TRUE;
                    }
                }

                sFileIo.close();

                if (XPR_IS_FALSE(sResult))
                    ::DeleteFile(aPath);
            }

            ::GlobalUnlock(sStgMedium.hGlobal);
        }

        ::ReleaseStgMedium(&sStgMedium);
    }

    if (XPR_IS_TRUE(sResult))
        ::SHChangeNotify(
            SHCNE_CREATE,
            SHCNF_PATH | SHCNF_FLUSH,
            aPath,
            XPR_NULL);

    return sResult;
}

xpr_bool_t DoPasteUnicodeText(
    LPDATAOBJECT aDataObject,
    const xpr_tchar_t *aPath)
{
    if (XPR_IS_NULL(aDataObject) || XPR_IS_NULL(aPath))
        return XPR_FALSE;

    xpr_bool_t sResult = XPR_FALSE;

    FORMATETC sTextFormatEtc =
        { CF_UNICODETEXT, XPR_NULL, DVASPECT_CONTENT, -1, TYMED_HGLOBAL };

    STGMEDIUM sStgMedium = {0};
    const HRESULT sComResult =
        aDataObject->GetData(&sTextFormatEtc, &sStgMedium);

    if (SUCCEEDED(sComResult))
    {
        xpr_wchar_t *sText =
            (xpr_wchar_t *)::GlobalLock(sStgMedium.hGlobal);
        if (XPR_IS_NOT_NULL(sText))
        {
            const xpr_ssize_t sTextBytes =
                (xpr_ssize_t)(wcslen(sText) * sizeof(xpr_wchar_t));
            xpr_sint_t sOpenMode =
                xpr::FileIo::OpenModeCreate |
                xpr::FileIo::OpenModeTruncate |
                xpr::FileIo::OpenModeWriteOnly;
            xpr::FileIo sFileIo;

            xpr_rcode_t sRcode = sFileIo.open(aPath, sOpenMode);
            if (XPR_RCODE_IS_SUCCESS(sRcode))
            {
                xpr_ushort_t sUnicodeBom = 0xFEFF;
                xpr_ssize_t sWritten = 0;
                sRcode =
                    sFileIo.write(
                        &sUnicodeBom,
                        sizeof(sUnicodeBom),
                        &sWritten);
                xpr_bool_t sWriteSucceeded =
                    XPR_RCODE_IS_SUCCESS(sRcode) &&
                    sWritten == sizeof(sUnicodeBom) ?
                    XPR_TRUE :
                    XPR_FALSE;

                if (XPR_IS_TRUE(sWriteSucceeded) &&
                    sTextBytes > 0)
                {
                    sWritten = 0;
                    sRcode =
                        sFileIo.write(
                            sText,
                            sTextBytes,
                            &sWritten);
                    sWriteSucceeded =
                        XPR_RCODE_IS_SUCCESS(sRcode) &&
                        sWritten == sTextBytes ?
                        XPR_TRUE :
                        XPR_FALSE;
                }

                sFileIo.close();
                sResult = sWriteSucceeded;

                if (XPR_IS_FALSE(sResult))
                    ::DeleteFile(aPath);
            }

            ::GlobalUnlock(sStgMedium.hGlobal);
        }

        ::ReleaseStgMedium(&sStgMedium);
    }

    if (XPR_IS_TRUE(sResult))
        ::SHChangeNotify(
            SHCNE_CREATE,
            SHCNF_PATH | SHCNF_FLUSH,
            aPath,
            XPR_NULL);

    return sResult;
}

xpr_bool_t DoPasteBitmap(
    LPDATAOBJECT aDataObject,
    const xpr_tchar_t *aPath)
{
    if (XPR_IS_NULL(aDataObject) || XPR_IS_NULL(aPath))
        return XPR_FALSE;

    xpr_bool_t sResult = XPR_FALSE;

    FORMATETC sBitmapFormatEtc =
        { CF_BITMAP, XPR_NULL, DVASPECT_CONTENT, -1, TYMED_GDI };

    STGMEDIUM sStgMedium = {0};
    const HRESULT sComResult =
        aDataObject->GetData(&sBitmapFormatEtc, &sStgMedium);

    if (SUCCEEDED(sComResult))
    {
        HBITMAP sBitmap = sStgMedium.hBitmap;
        if (XPR_IS_NOT_NULL(sBitmap))
        {
            HWND sHwnd = ::GetDesktopWindow();
            HDC sDC = ::GetDC(sHwnd);
            if (XPR_IS_NOT_NULL(sDC))
            {
                sResult =
                    WriteBitmapFile(
                        aPath,
                        sBitmap,
                        sDC);
                ::ReleaseDC(sHwnd, sDC);
            }
        }

        // The STGMEDIUM returned by IDataObject owns the bitmap even when
        // pUnkForRelease is NULL. ReleaseStgMedium handles both ownership
        // forms; deleting hBitmap directly would double-free delegated media.
        ::ReleaseStgMedium(&sStgMedium);
    }

    if (XPR_IS_TRUE(sResult))
        ::SHChangeNotify(
            SHCNE_CREATE,
            SHCNF_PATH | SHCNF_FLUSH,
            aPath,
            XPR_NULL);

    return sResult;
}

xpr_bool_t DoPasteDIB(
    LPDATAOBJECT aDataObject,
    const xpr_tchar_t *aPath)
{
    if (XPR_IS_NULL(aDataObject) || XPR_IS_NULL(aPath))
        return XPR_FALSE;

    xpr_bool_t sResult = XPR_FALSE;

    FORMATETC sDibFormatEtc =
        { CF_DIB, XPR_NULL, DVASPECT_CONTENT, -1, TYMED_HGLOBAL };

    STGMEDIUM sStgMedium = {0};
    const HRESULT sComResult =
        aDataObject->GetData(&sDibFormatEtc, &sStgMedium);

    if (SUCCEEDED(sComResult))
    {
        LPBITMAPINFO sBitmapInfo =
            (LPBITMAPINFO)::GlobalLock(sStgMedium.hGlobal);
        if (XPR_IS_NOT_NULL(sBitmapInfo))
        {
            sResult =
                WriteBitmapFile(
                    aPath,
                    sBitmapInfo);
            ::GlobalUnlock(sStgMedium.hGlobal);
        }

        ::ReleaseStgMedium(&sStgMedium);
    }

    if (XPR_IS_TRUE(sResult))
        ::SHChangeNotify(
            SHCNE_CREATE,
            SHCNF_PATH | SHCNF_FLUSH,
            aPath,
            XPR_NULL);

    return sResult;
}

xpr_bool_t GetPreferredDropEffect(CLIPFORMAT aPreferredDropEffectClipFormat, DROPEFFECT &aDropEffect)
{
    COleDataObject sOleDataObject;
    if (sOleDataObject.AttachClipboard() == XPR_FALSE)
        return XPR_FALSE;

    return GetPreferredDropEffect(&sOleDataObject, aPreferredDropEffectClipFormat, aDropEffect);
}

xpr_bool_t GetPreferredDropEffect(COleDataObject *aOleDataObject, CLIPFORMAT aPreferredDropEffectClipFormat, DROPEFFECT &aDropEffect)
{
    if (XPR_IS_NULL(aOleDataObject))
        return XPR_FALSE;

    HGLOBAL sGlobal = aOleDataObject->GetGlobalData(aPreferredDropEffectClipFormat);
    if (XPR_IS_NULL(sGlobal))
        return XPR_FALSE;

    aDropEffect = *((DROPEFFECT *)::GlobalLock(sGlobal));

    ::GlobalUnlock(sGlobal);

    return XPR_TRUE;
}

xpr_bool_t IsPasteDIB(COleDataObject *aOleDataObject)
{
    if (XPR_IS_NULL(aOleDataObject))
        return XPR_FALSE;

    if (aOleDataObject->IsDataAvailable((CLIPFORMAT)CF_DIB) == XPR_TRUE)
        return XPR_TRUE;

    return XPR_FALSE;
}

xpr_bool_t IsPasteBitmap(COleDataObject *aOleDataObject)
{
    if (XPR_IS_NULL(aOleDataObject))
        return XPR_FALSE;

    if (aOleDataObject->IsDataAvailable((CLIPFORMAT)CF_BITMAP) == XPR_TRUE)
        return XPR_TRUE;

    return XPR_FALSE;
}

xpr_bool_t IsPasteText(COleDataObject *aOleDataObject)
{
    if (XPR_IS_NULL(aOleDataObject))
        return XPR_FALSE;

    if (aOleDataObject->IsDataAvailable((CLIPFORMAT)CF_TEXT) == XPR_TRUE)
        return XPR_TRUE;

    return XPR_FALSE;
}

xpr_bool_t IsPasteUnicodeText(COleDataObject *aOleDataObject)
{
    if (XPR_IS_NULL(aOleDataObject))
        return XPR_FALSE;

    if (aOleDataObject->IsDataAvailable((CLIPFORMAT)CF_UNICODETEXT) == XPR_TRUE)
        return XPR_TRUE;

    return XPR_FALSE;
}

xpr_bool_t IsPasteShellIdList(COleDataObject *aOleDataObject, CLIPFORMAT aShellIDListClipFormat)
{
    XPR_ASSERT(aOleDataObject != XPR_NULL);

    if (aOleDataObject->IsDataAvailable((CLIPFORMAT)aShellIDListClipFormat) == XPR_TRUE)
    {
        return XPR_TRUE;
    }

    return XPR_FALSE;
}

xpr_bool_t IsPasteInetUrl(COleDataObject *aOleDataObject, CLIPFORMAT aInetUrlClipFormat, CLIPFORMAT aFileContentsClipFormat, CLIPFORMAT aFileDescriptorClipFormat)
{
    if (XPR_IS_NULL(aOleDataObject))
        return XPR_FALSE;

    if (aOleDataObject->IsDataAvailable((CLIPFORMAT)aInetUrlClipFormat)        == XPR_TRUE &&
        aOleDataObject->IsDataAvailable((CLIPFORMAT)aFileContentsClipFormat)   == XPR_TRUE &&
        aOleDataObject->IsDataAvailable((CLIPFORMAT)aFileDescriptorClipFormat) == XPR_TRUE &&
        GetDataObjectFormatCount(aOleDataObject) >= 3)
    {
        return XPR_TRUE;
    }

    return XPR_FALSE;
}

xpr_bool_t DoPasteInetUrl(
    LPDATAOBJECT aDataObject,
    xpr_tchar_t *aDir,
    CLIPFORMAT aInetUrlClipFormat,
    CLIPFORMAT aFileContentsClipFormat,
    CLIPFORMAT aFileDescriptorClipFormat,
    xpr_bool_t aUnicode)
{
    if (XPR_IS_NULL(aDataObject) || XPR_IS_NULL(aDir))
        return XPR_FALSE;

    xpr_bool_t sResult = XPR_FALSE;

    FORMATETC sInetUrlFormatEtc =
        { aInetUrlClipFormat, XPR_NULL, DVASPECT_CONTENT, -1, TYMED_HGLOBAL };
    FORMATETC sDescriptorFormatEtc =
        { aFileDescriptorClipFormat, XPR_NULL, DVASPECT_CONTENT, -1, TYMED_HGLOBAL };
    FORMATETC sContentsFormatEtc =
        { aFileContentsClipFormat, XPR_NULL, DVASPECT_CONTENT, -1, TYMED_HGLOBAL | TYMED_ISTREAM };

    STGMEDIUM sInetUrlStgMedium = {0};
    STGMEDIUM sDescriptorStgMedium = {0};

    const HRESULT sInetResult =
        aDataObject->GetData(
            &sInetUrlFormatEtc,
            &sInetUrlStgMedium);
    const HRESULT sDescriptorResult =
        aDataObject->GetData(
            &sDescriptorFormatEtc,
            &sDescriptorStgMedium);

    xpr_tchar_t *sUrl = XPR_NULL;
    FILEGROUPDESCRIPTORA *sFileGroupDescA = XPR_NULL;
    FILEGROUPDESCRIPTORW *sFileGroupDescW = XPR_NULL;

    if (SUCCEEDED(sInetResult) &&
        SUCCEEDED(sDescriptorResult) &&
        XPR_IS_NOT_NULL(sInetUrlStgMedium.hGlobal) &&
        XPR_IS_NOT_NULL(sDescriptorStgMedium.hGlobal))
    {
        sUrl =
            (xpr_tchar_t *)::GlobalLock(
                sInetUrlStgMedium.hGlobal);

        if (XPR_IS_TRUE(aUnicode))
        {
            sFileGroupDescW =
                (FILEGROUPDESCRIPTORW *)::GlobalLock(
                    sDescriptorStgMedium.hGlobal);
        }
        else
        {
            sFileGroupDescA =
                (FILEGROUPDESCRIPTORA *)::GlobalLock(
                    sDescriptorStgMedium.hGlobal);
        }

        if (XPR_IS_NOT_NULL(sUrl) &&
            (XPR_IS_NOT_NULL(sFileGroupDescA) ||
             XPR_IS_NOT_NULL(sFileGroupDescW)))
        {
            RemoveLastSplit(aDir);

            const xpr_sint_t sCount =
                XPR_IS_TRUE(aUnicode) ?
                sFileGroupDescW->cItems :
                sFileGroupDescA->cItems;

            for (xpr_sint_t i = 0; i < sCount; ++i)
            {
                FILEDESCRIPTORA *sFileDescA = XPR_NULL;
                FILEDESCRIPTORW *sFileDescW = XPR_NULL;
                if (XPR_IS_TRUE(aUnicode))
                    sFileDescW = &sFileGroupDescW->fgd[i];
                else
                    sFileDescA = &sFileGroupDescA->fgd[i];

                xpr_tchar_t sFileName[XPR_MAX_PATH + 1] = {0};
                xpr_size_t sInputBytes =
                    XPR_IS_TRUE(aUnicode) ?
                    wcslen(sFileDescW->cFileName) * sizeof(xpr_wchar_t) :
                    strlen(sFileDescA->cFileName) * sizeof(xpr_char_t);
                xpr_size_t sOutputBytes =
                    XPR_MAX_PATH * sizeof(xpr_tchar_t);

                if (XPR_IS_TRUE(aUnicode))
                {
                    XPR_UTF16_TO_TCS(
                        sFileDescW->cFileName,
                        &sInputBytes,
                        sFileName,
                        &sOutputBytes);
                }
                else
                {
                    XPR_MBS_TO_TCS(
                        sFileDescA->cFileName,
                        &sInputBytes,
                        sFileName,
                        &sOutputBytes);
                }
                sFileName[sOutputBytes / sizeof(xpr_tchar_t)] = 0;

                xpr_tchar_t sExt[XPR_MAX_PATH + 1] = {0};
                SplitFileNameExt(sFileName, sFileName, sExt);

                xpr_tchar_t sPath[XPR_MAX_PATH + 1] = {0};
                SetNewPath(sPath, aDir, sFileName, sExt);

                sContentsFormatEtc.lindex = i;
                STGMEDIUM sContentMedium = {0};
                const HRESULT sContentResult =
                    aDataObject->GetData(
                        &sContentsFormatEtc,
                        &sContentMedium);

                if (SUCCEEDED(sContentResult))
                {
                    xpr_bool_t sFileSucceeded = XPR_FALSE;

                    if (sContentMedium.tymed == TYMED_HGLOBAL &&
                        XPR_IS_NOT_NULL(sContentMedium.hGlobal))
                    {
                        xpr_char_t *sData =
                            (xpr_char_t *)::GlobalLock(
                                sContentMedium.hGlobal);
                        if (XPR_IS_NOT_NULL(sData))
                        {
                            xpr_ssize_t sLength =
                                XPR_IS_TRUE(aUnicode) ?
                                (xpr_ssize_t)sFileDescW->nFileSizeLow :
                                (xpr_ssize_t)sFileDescA->nFileSizeLow;
                            if (sLength == 0)
                            {
                                sLength =
                                    (xpr_ssize_t)::GlobalSize(
                                        sContentMedium.hGlobal);
                            }

                            xpr::FileIo sFileIo;
                            const xpr_sint_t sOpenMode =
                                xpr::FileIo::OpenModeCreate |
                                xpr::FileIo::OpenModeTruncate |
                                xpr::FileIo::OpenModeWriteOnly;
                            xpr_rcode_t sRcode =
                                sFileIo.open(sPath, sOpenMode);
                            if (XPR_RCODE_IS_SUCCESS(sRcode))
                            {
                                xpr_ssize_t sWritten = 0;
                                sRcode =
                                    sFileIo.write(
                                        sData,
                                        sLength,
                                        &sWritten);
                                sFileIo.close();

                                if (XPR_RCODE_IS_SUCCESS(sRcode) &&
                                    sWritten == sLength)
                                {
                                    sFileSucceeded = XPR_TRUE;
                                }
                                else
                                {
                                    ::DeleteFile(sPath);
                                }
                            }

                            ::GlobalUnlock(sContentMedium.hGlobal);
                        }
                    }
                    else if (sContentMedium.tymed == TYMED_ISTREAM &&
                             XPR_IS_NOT_NULL(sContentMedium.pstm))
                    {
                        if (SUCCEEDED(
                                StreamToFile(
                                    sContentMedium.pstm,
                                    sPath)))
                        {
                            sFileSucceeded = XPR_TRUE;
                        }
                    }

                    ::ReleaseStgMedium(&sContentMedium);

                    if (XPR_IS_TRUE(sFileSucceeded))
                    {
                        ::SHChangeNotify(
                            SHCNE_CREATE,
                            SHCNF_PATH | SHCNF_FLUSH,
                            sPath,
                            XPR_NULL);
                        sResult = XPR_TRUE;
                    }
                }
            }
        }
    }

    if (XPR_IS_NOT_NULL(sUrl))
        ::GlobalUnlock(sInetUrlStgMedium.hGlobal);

    if (XPR_IS_NOT_NULL(sFileGroupDescA) ||
        XPR_IS_NOT_NULL(sFileGroupDescW))
    {
        ::GlobalUnlock(sDescriptorStgMedium.hGlobal);
    }

    if (SUCCEEDED(sInetResult))
        ::ReleaseStgMedium(&sInetUrlStgMedium);
    if (SUCCEEDED(sDescriptorResult))
        ::ReleaseStgMedium(&sDescriptorStgMedium);

    return sResult;
}

xpr_bool_t IsPasteFileContents(COleDataObject *aOleDataObject, CLIPFORMAT aFileContentsClipFormat, CLIPFORMAT aFileDescriptorClipFormat)
{
    if (XPR_IS_NULL(aOleDataObject))
        return XPR_FALSE;

    if (aOleDataObject->IsDataAvailable((CLIPFORMAT)aFileContentsClipFormat)   == XPR_TRUE &&
        aOleDataObject->IsDataAvailable((CLIPFORMAT)aFileDescriptorClipFormat) == XPR_TRUE &&
        GetDataObjectFormatCount(aOleDataObject) >= 2)
    {
        return XPR_TRUE;
    }

    return XPR_FALSE;
}

//
// outlook
//
xpr_bool_t DoPasteFileContents(
    LPDATAOBJECT aDataObject,
    xpr_tchar_t *aDir,
    CLIPFORMAT aFileContentsClipFormat,
    CLIPFORMAT aFileDescriptorClipFormat,
    xpr_bool_t aUnicode)
{
    if (XPR_IS_NULL(aDataObject) || XPR_IS_NULL(aDir))
        return XPR_FALSE;

    xpr_bool_t sResult = XPR_FALSE;

    FILEGROUPDESCRIPTORA *sFileGroupDescA = XPR_NULL;
    FILEGROUPDESCRIPTORW *sFileGroupDescW = XPR_NULL;

    FORMATETC sDescriptorFormatEtc =
        { aFileDescriptorClipFormat, XPR_NULL, DVASPECT_CONTENT, -1, TYMED_HGLOBAL };
    FORMATETC sContentsFormatEtc =
        { aFileContentsClipFormat, XPR_NULL, DVASPECT_CONTENT, -1, TYMED_ISTREAM | TYMED_ISTORAGE };

    STGMEDIUM sDescriptorMedium = {0};
    const HRESULT sDescriptorResult =
        aDataObject->GetData(
            &sDescriptorFormatEtc,
            &sDescriptorMedium);

    if (SUCCEEDED(sDescriptorResult) &&
        XPR_IS_NOT_NULL(sDescriptorMedium.hGlobal))
    {
        if (XPR_IS_TRUE(aUnicode))
        {
            sFileGroupDescW =
                (FILEGROUPDESCRIPTORW *)::GlobalLock(
                    sDescriptorMedium.hGlobal);
        }
        else
        {
            sFileGroupDescA =
                (FILEGROUPDESCRIPTORA *)::GlobalLock(
                    sDescriptorMedium.hGlobal);
        }

        if (XPR_IS_NOT_NULL(sFileGroupDescA) ||
            XPR_IS_NOT_NULL(sFileGroupDescW))
        {
            RemoveLastSplit(aDir);

            const xpr_sint_t sCount =
                XPR_IS_TRUE(aUnicode) ?
                sFileGroupDescW->cItems :
                sFileGroupDescA->cItems;

            for (xpr_sint_t i = 0; i < sCount; ++i)
            {
                FILEDESCRIPTORA *sFileDescA = XPR_NULL;
                FILEDESCRIPTORW *sFileDescW = XPR_NULL;
                if (XPR_IS_TRUE(aUnicode))
                    sFileDescW = &sFileGroupDescW->fgd[i];
                else
                    sFileDescA = &sFileGroupDescA->fgd[i];

                xpr_tchar_t sFileName[XPR_MAX_PATH + 1] = {0};
                xpr_size_t sInputBytes =
                    XPR_IS_TRUE(aUnicode) ?
                    wcslen(sFileDescW->cFileName) * sizeof(xpr_wchar_t) :
                    strlen(sFileDescA->cFileName) * sizeof(xpr_char_t);
                xpr_size_t sOutputBytes =
                    XPR_MAX_PATH * sizeof(xpr_tchar_t);

                if (XPR_IS_TRUE(aUnicode))
                {
                    XPR_UTF16_TO_TCS(
                        sFileDescW->cFileName,
                        &sInputBytes,
                        sFileName,
                        &sOutputBytes);
                }
                else
                {
                    XPR_MBS_TO_TCS(
                        sFileDescA->cFileName,
                        &sInputBytes,
                        sFileName,
                        &sOutputBytes);
                }
                sFileName[sOutputBytes / sizeof(xpr_tchar_t)] = 0;

                xpr_tchar_t sExt[XPR_MAX_PATH + 1] = {0};
                SplitFileNameExt(sFileName, sFileName, sExt);

                xpr_tchar_t sPath[XPR_MAX_PATH + 1] = {0};
                SetNewPath(sPath, aDir, sFileName, sExt);

                sContentsFormatEtc.lindex = i;
                STGMEDIUM sFileMedium = {0};
                const HRESULT sFileResult =
                    aDataObject->GetData(
                        &sContentsFormatEtc,
                        &sFileMedium);

                if (SUCCEEDED(sFileResult))
                {
                    HRESULT sSaveResult = E_FAIL;
                    if (sFileMedium.tymed == TYMED_ISTORAGE &&
                        XPR_IS_NOT_NULL(sFileMedium.pstg))
                    {
                        sSaveResult =
                            StorageToFile(
                                sFileMedium.pstg,
                                sPath);
                    }
                    else if (sFileMedium.tymed == TYMED_ISTREAM &&
                             XPR_IS_NOT_NULL(sFileMedium.pstm))
                    {
                        sSaveResult =
                            StreamToFile(
                                sFileMedium.pstm,
                                sPath);
                    }

                    ::ReleaseStgMedium(&sFileMedium);

                    if (SUCCEEDED(sSaveResult))
                    {
                        ::SHChangeNotify(
                            SHCNE_CREATE,
                            SHCNF_PATH | SHCNF_FLUSH,
                            sPath,
                            XPR_NULL);
                        sResult = XPR_TRUE;
                    }
                }
            }
        }

        if (XPR_IS_NOT_NULL(sFileGroupDescA) ||
            XPR_IS_NOT_NULL(sFileGroupDescW))
        {
            ::GlobalUnlock(sDescriptorMedium.hGlobal);
        }

        ::ReleaseStgMedium(&sDescriptorMedium);
    }
    else if (SUCCEEDED(sDescriptorResult))
    {
        ::ReleaseStgMedium(&sDescriptorMedium);
    }

    return sResult;
}

void SetTextClipboard(HWND aHwndOwner, const xpr_tchar_t *aText)
{
#ifdef _UNICODE
    SetTextClipboardW(aHwndOwner, aText);
#else
    SetTextClipboardA(aHwndOwner, aText);
#endif
}

void SetTextClipboardA(HWND aHwndOwner, const xpr_char_t *aText)
{
    if (XPR_IS_NULL(aText))
        return;

    if (!::OpenClipboard(aHwndOwner))
        return;

    xpr_sint_t sSize = (xpr_sint_t)strlen(aText) + 1;

    HANDLE sGlobal = ::GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, sSize);
    if (XPR_IS_NOT_NULL(sGlobal))
    {
        xpr_byte_t *sData = (xpr_byte_t *)::GlobalLock(sGlobal);
        if (XPR_IS_NOT_NULL(sData))
        {
            ::EmptyClipboard();

            memcpy(sData, aText, sSize);

            ::GlobalUnlock(sGlobal);
            ::SetClipboardData(CF_TEXT, sGlobal);
        }
        else
        {
            ::GlobalFree(sGlobal);
        }
    }

    ::CloseClipboard();
}

void SetTextClipboardW(HWND aHwndOwner, const xpr_tchar_t *aText)
{
    if (XPR_IS_NULL(aText))
        return;

    if (::OpenClipboard(aHwndOwner) == XPR_FALSE)
        return;

    xpr_sint_t sSize = (xpr_sint_t)((_tcslen(aText) + 1) * sizeof(xpr_wchar_t));

    HANDLE sGlobal = ::GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, sSize);
    if (XPR_IS_NOT_NULL(sGlobal))
    {
        xpr_byte_t *sData = (xpr_byte_t *)::GlobalLock(sGlobal);
        if (XPR_IS_NOT_NULL(sData))
        {
            ::EmptyClipboard();

            memcpy(sData, aText, sSize);

            ::GlobalUnlock(sGlobal);
            ::SetClipboardData(CF_UNICODETEXT, sGlobal);
        }
        else
        {
            ::GlobalFree(sGlobal);
        }
    }

    ::CloseClipboard();
}
} // namespace fxfile
