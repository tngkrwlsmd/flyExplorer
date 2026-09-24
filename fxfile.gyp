#
# Copyright (c) 2013 Leon Lee author. All rights reserved.
#
#   homepage: http://www.flychk.com
#   e-mail:   mailto:flychk@flychk.com
#
# Use of this source code is governed by a GPLv3 license that can be
# found in the LICENSE file.

{
    'targets':
    [
        {
            'target_name': 'fxfile',

            'type': 'none',

            # This is the solution aggregate/umbrella project.  It does not
            # compile sources itself, but Visual Studio still requires it to
            # expose every solution configuration that can be selected.
            'default_configuration': 'Debug-x86-Unicode',

            'configurations':
            {
                'Debug-x86-Unicode':
                {
                    'msvs_configuration_platform': 'Win32',
                },

                'Release-x86-Unicode':
                {
                    'msvs_configuration_platform': 'Win32',
                },

                'Debug-x86-Multibyte':
                {
                    'msvs_configuration_platform': 'Win32',
                },

                'Release-x86-Multibyte':
                {
                    'msvs_configuration_platform': 'Win32',
                },

                'conditions':
                [
                    [ 'target_arch!="x86"',
                        {
                            'Debug-x64-Unicode':
                            {
                                'msvs_configuration_platform': 'x64',
                            },

                            'Release-x64-Unicode':
                            {
                                'msvs_configuration_platform': 'x64',
                            },
                        },
                    ],
                ],
            },

            'dependencies':
            [
                'src/xpr/xpr.gyp:*',
                'src/fxfile/fxfile.gyp:*',
                'src/fxfile-tests/fxfile-tests.gyp:*',
                'src/fxfile-crash/fxfile-crash.gyp:*',
                'src/fxfile-launcher/fxfile-launcher.gyp:*',
            ],
        }
    ]
}
