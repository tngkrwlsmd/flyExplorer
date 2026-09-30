//
// Copyright (c) 2001-2012 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "bitmap.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
namespace
{
xpr_bool_t WriteFileExact(
    HANDLE aFile,
    const void *aData,
    DWORD aSize)
{
    if (aSize == 0)
        return XPR_TRUE;

    if (aFile == INVALID_HANDLE_VALUE || XPR_IS_NULL(aData))
        return XPR_FALSE;

    DWORD sWrittenBytes = 0;
    if (::WriteFile(
            aFile,
            aData,
            aSize,
            &sWrittenBytes,
            XPR_NULL) == FALSE)
    {
        return XPR_FALSE;
    }

    return sWrittenBytes == aSize ? XPR_TRUE : XPR_FALSE;
}
} // namespace

// reference : https://msdn.microsoft.com/ko-kr/library/windows/desktop/dd145119%28v=vs.85%29.aspx?f=255&MSPPError=-2147217396
BITMAPINFO *CreateBitmapInfoStruct(HBITMAP aBitmap)
{
    BITMAP sBitmapHeader = {0};
    if (GetObject(aBitmap, sizeof(BITMAP), (xpr_char_t *)&sBitmapHeader) == XPR_FALSE)
        return XPR_NULL;

    BITMAPINFO *sBitmapInfo = XPR_NULL;
    xpr_sint_t sColorBits = sBitmapHeader.bmPlanes * sBitmapHeader.bmBitsPixel;

    if (sColorBits == 1)       sColorBits = 1;
    else if (sColorBits <= 4)  sColorBits = 4;
    else if (sColorBits <= 8)  sColorBits = 8;
    else if (sColorBits <= 16) sColorBits = 16;
    else if (sColorBits <= 24) sColorBits = 24;
    else                       sColorBits = 32;

    if (sColorBits < 24)
        sBitmapInfo = (BITMAPINFO *)malloc(sizeof(BITMAPINFOHEADER) + sizeof(RGBQUAD) * (xpr_sint_t)(1 << sColorBits));
    else
        sBitmapInfo = (BITMAPINFO *)malloc(sizeof(BITMAPINFOHEADER));

    if (XPR_IS_NULL(sBitmapInfo))
        return XPR_NULL;

    sBitmapInfo->bmiHeader.biSize         = sizeof(BITMAPINFOHEADER);
    sBitmapInfo->bmiHeader.biWidth        = sBitmapHeader.bmWidth;
    sBitmapInfo->bmiHeader.biHeight       = sBitmapHeader.bmHeight;
    sBitmapInfo->bmiHeader.biPlanes       = sBitmapHeader.bmPlanes;
    sBitmapInfo->bmiHeader.biBitCount     = sBitmapHeader.bmBitsPixel;
    sBitmapInfo->bmiHeader.biCompression  = BI_RGB;
    sBitmapInfo->bmiHeader.biSizeImage    = ((sBitmapInfo->bmiHeader.biWidth * sColorBits +31) & ~31) / 8 * sBitmapInfo->bmiHeader.biHeight;
    sBitmapInfo->bmiHeader.biClrImportant = 0;

    if (sColorBits < 24)
        sBitmapInfo->bmiHeader.biClrUsed = (1 << sColorBits);

    return sBitmapInfo;
}

xpr_bool_t WriteBitmapFile(const xpr_tchar_t *aFile, BITMAPINFO *aBitmapInfo)
{
    if (XPR_IS_NULL(aFile) || XPR_IS_NULL(aBitmapInfo))
        return XPR_FALSE;

    BITMAPINFOHEADER *sBitmapInfoHeader = (BITMAPINFOHEADER *)aBitmapInfo;
    xpr_byte_t *sBits = (xpr_byte_t *)aBitmapInfo + sizeof(BITMAPINFOHEADER) + (sizeof(RGBQUAD) * sBitmapInfoHeader->biClrUsed);

    xpr_bool_t sResult = XPR_FALSE;

    {
        // Create the .BMP file.
        HANDLE sFile = ::CreateFile(
            aFile,
            GENERIC_READ | GENERIC_WRITE,
            (DWORD)0,
            XPR_NULL,
            CREATE_ALWAYS,
            FILE_ATTRIBUTE_NORMAL,
            (HANDLE)XPR_NULL);

        if (sFile != INVALID_HANDLE_VALUE)
        {
            BITMAPFILEHEADER sBitmapFileHeader = {0};
            sBitmapFileHeader.bfType = 0x4d42; // 0x42 = "B" 0x4d = "M"
            sBitmapFileHeader.bfSize = (DWORD)(sizeof(BITMAPFILEHEADER) + sBitmapInfoHeader->biSize + sBitmapInfoHeader->biClrUsed * sizeof(RGBQUAD) + sBitmapInfoHeader->biSizeImage);
            sBitmapFileHeader.bfReserved1 = 0;
            sBitmapFileHeader.bfReserved2 = 0;
            sBitmapFileHeader.bfOffBits = (DWORD)sizeof(BITMAPFILEHEADER) + sBitmapInfoHeader->biSize + sBitmapInfoHeader->biClrUsed * sizeof(RGBQUAD);

            const DWORD sBitmapInfoSize =
                (DWORD)(sizeof(BITMAPINFOHEADER) +
                        sBitmapInfoHeader->biClrUsed * sizeof(RGBQUAD));

            sResult =
                XPR_IS_TRUE(
                    WriteFileExact(
                        sFile,
                        &sBitmapFileHeader,
                        sizeof(BITMAPFILEHEADER))) &&
                XPR_IS_TRUE(
                    WriteFileExact(
                        sFile,
                        sBitmapInfoHeader,
                        sBitmapInfoSize)) &&
                XPR_IS_TRUE(
                    WriteFileExact(
                        sFile,
                        sBits,
                        sBitmapInfoHeader->biSizeImage)) ?
                XPR_TRUE :
                XPR_FALSE;

            ::CloseHandle(sFile);

            if (XPR_IS_FALSE(sResult))
                ::DeleteFile(aFile);
        }
    }

    return sResult;
}

xpr_bool_t WriteBitmapFile(const xpr_tchar_t *aFile, BITMAPINFO *aBitmapInfo, HBITMAP aBitmap, HDC aDC)
{
    if (XPR_IS_NULL(aFile) || XPR_IS_NULL(aBitmapInfo) || XPR_IS_NULL(aBitmap) || XPR_IS_NULL(aDC))
        return XPR_FALSE;

    BITMAPINFOHEADER *sBitmapInfoHeader = (BITMAPINFOHEADER *)aBitmapInfo;
    xpr_byte_t *sBits = (xpr_byte_t *)GlobalAlloc(GMEM_FIXED, sBitmapInfoHeader->biSizeImage);
    if (XPR_IS_NULL(sBits))
        return XPR_FALSE;

    xpr_bool_t sResult = XPR_FALSE;

    xpr_sint_t sCopiedLines = GetDIBits(aDC, aBitmap, 0, (WORD)sBitmapInfoHeader->biHeight, sBits, aBitmapInfo, DIB_RGB_COLORS);
    if (sCopiedLines != 0 && XPR_IS_NOT_NULL(sBits))
    {
        // Create the .BMP file.
        HANDLE sFile = ::CreateFile(
            aFile,
            GENERIC_READ | GENERIC_WRITE,
            (DWORD)0,
            XPR_NULL,
            CREATE_ALWAYS,
            FILE_ATTRIBUTE_NORMAL,
            (HANDLE)XPR_NULL);

        if (sFile != INVALID_HANDLE_VALUE)
        {
            BITMAPFILEHEADER sBitmapFileHeader = {0};
            sBitmapFileHeader.bfType = 0x4d42; // 0x42 = "B" 0x4d = "M"
            sBitmapFileHeader.bfSize = (DWORD)(sizeof(BITMAPFILEHEADER) + sBitmapInfoHeader->biSize + sBitmapInfoHeader->biClrUsed * sizeof(RGBQUAD) + sBitmapInfoHeader->biSizeImage);
            sBitmapFileHeader.bfReserved1 = 0;
            sBitmapFileHeader.bfReserved2 = 0;
            sBitmapFileHeader.bfOffBits = (DWORD)sizeof(BITMAPFILEHEADER) + sBitmapInfoHeader->biSize + sBitmapInfoHeader->biClrUsed * sizeof(RGBQUAD);

            const DWORD sBitmapInfoSize =
                (DWORD)(sizeof(BITMAPINFOHEADER) +
                        sBitmapInfoHeader->biClrUsed * sizeof(RGBQUAD));

            sResult =
                XPR_IS_TRUE(
                    WriteFileExact(
                        sFile,
                        &sBitmapFileHeader,
                        sizeof(BITMAPFILEHEADER))) &&
                XPR_IS_TRUE(
                    WriteFileExact(
                        sFile,
                        sBitmapInfoHeader,
                        sBitmapInfoSize)) &&
                XPR_IS_TRUE(
                    WriteFileExact(
                        sFile,
                        sBits,
                        sBitmapInfoHeader->biSizeImage)) ?
                XPR_TRUE :
                XPR_FALSE;

            ::CloseHandle(sFile);

            if (XPR_IS_FALSE(sResult))
                ::DeleteFile(aFile);
        }
    }

    ::GlobalFree((HGLOBAL)sBits);

    return sResult;
}

xpr_bool_t WriteBitmapFile(const xpr_tchar_t *aFile, HBITMAP aBitmap, HDC aDC)
{
    if (XPR_IS_NULL(aFile) || XPR_IS_NULL(aBitmap) || XPR_IS_NULL(aDC))
        return XPR_FALSE;

    xpr_bool_t sResult = XPR_FALSE;

    BITMAPINFO *sBitmapInfo = CreateBitmapInfoStruct(aBitmap);
    if (XPR_IS_NOT_NULL(sBitmapInfo))
    {
        sResult = WriteBitmapFile(aFile, sBitmapInfo, aBitmap, aDC);

        free(sBitmapInfo);
    }

    return sResult;
}

xpr_bool_t WriteBitmapFile(const xpr_tchar_t *aFile, HDC aDC, LPCRECT aRect)
{
    if (XPR_IS_NULL(aFile) || XPR_IS_NULL(aDC) || XPR_IS_NULL(aRect))
        return XPR_FALSE;

    CDC *sDC = CDC::FromHandle(aDC);
    if (XPR_IS_NULL(sDC))
        return XPR_FALSE;

    CRect sRect(aRect);

    CDC sMemDC;
    if (sMemDC.CreateCompatibleDC(sDC) == XPR_FALSE)
        return XPR_FALSE;

    CBitmap sBitmap;
    if (sBitmap.CreateCompatibleBitmap(
            sDC,
            sRect.Width(),
            sRect.Height()) == XPR_FALSE)
    {
        return XPR_FALSE;
    }

    CBitmap *sOldBitmap = sMemDC.SelectObject(&sBitmap);
    if (XPR_IS_NULL(sOldBitmap))
        return XPR_FALSE;

    xpr_bool_t sResult = XPR_FALSE;
    if (sMemDC.BitBlt(
            0,
            0,
            sRect.Width(),
            sRect.Height(),
            sDC,
            0,
            0,
            SRCCOPY) != XPR_FALSE)
    {
        sResult = WriteBitmapFile(aFile, sBitmap, aDC);
    }

    sMemDC.SelectObject(sOldBitmap);

    return sResult;
}
} // namespace fxfile
