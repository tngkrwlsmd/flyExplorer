#
# Copyright (c) 2026 flyExplorer contributors.
#
# Native product functional regression target.
#

{
    'includes':
    [
        '../../build/common.gypi',
    ],

    'target_defaults':
    {
        'default_configuration': 'Debug-x86-Unicode',

        'configurations':
        {
            'Debug-x86-Unicode':
            {
                'inherit_from': ['Debug-x86-Unicode_Base'],
                'msvs_configuration_attributes':
                {
                    'OutputDirectory': '../../bin/x86-unicode',
                    'IntermediateDirectory': '../../obj/fxfile-functional-tests/dbg-x86-unicode',
                },
                'msvs_settings':
                {
                    'VCLinkerTool':
                    {
                        'SubSystem': 1,
                        'OutputFile': '$(OutDir)\\fxfile-functional-tests_dbg.exe',
                        'AdditionalLibraryDirectories': ['$(OutDir)'],
                        'AdditionalDependencies': ['libxprw_dbg.lib', 'shell32.lib'],
                    },
                },
            },

            'Release-x86-Unicode':
            {
                'inherit_from': ['Release-x86-Unicode_Base'],
                'msvs_configuration_attributes':
                {
                    'OutputDirectory': '../../bin/x86-unicode',
                    'IntermediateDirectory': '../../obj/fxfile-functional-tests/rel-x86-unicode',
                },
                'msvs_settings':
                {
                    'VCLinkerTool':
                    {
                        'SubSystem': 1,
                        'OutputFile': '$(OutDir)\\fxfile-functional-tests.exe',
                        'AdditionalLibraryDirectories': ['$(OutDir)'],
                        'AdditionalDependencies': ['libxprw.lib', 'shell32.lib'],
                    },
                },
            },

            'Debug-x86-Multibyte':
            {
                'inherit_from': ['Debug-x86-Multibyte_Base'],
                'msvs_configuration_attributes':
                {
                    'OutputDirectory': '../../bin/x86-multibyte',
                    'IntermediateDirectory': '../../obj/fxfile-functional-tests/dbg-x86-multibyte',
                },
                'msvs_settings':
                {
                    'VCLinkerTool':
                    {
                        'SubSystem': 1,
                        'OutputFile': '$(OutDir)\\fxfile-functional-tests_dbg.exe',
                        'AdditionalLibraryDirectories': ['$(OutDir)'],
                        'AdditionalDependencies': ['libxpr_dbg.lib', 'shell32.lib'],
                    },
                },
            },

            'Release-x86-Multibyte':
            {
                'inherit_from': ['Release-x86-Multibyte_Base'],
                'msvs_configuration_attributes':
                {
                    'OutputDirectory': '../../bin/x86-multibyte',
                    'IntermediateDirectory': '../../obj/fxfile-functional-tests/rel-x86-multibyte',
                },
                'msvs_settings':
                {
                    'VCLinkerTool':
                    {
                        'SubSystem': 1,
                        'OutputFile': '$(OutDir)\\fxfile-functional-tests.exe',
                        'AdditionalLibraryDirectories': ['$(OutDir)'],
                        'AdditionalDependencies': ['libxpr.lib', 'shell32.lib'],
                    },
                },
            },

            'conditions':
            [
                [ 'target_arch!="x86"',
                    {
                        'Debug-x64-Unicode':
                        {
                            'inherit_from': ['Debug-x64-Unicode_Base'],
                            'msvs_configuration_attributes':
                            {
                                'OutputDirectory': '../../bin/x64',
                                'IntermediateDirectory': '../../obj/fxfile-functional-tests/dbg-x64',
                            },
                            'msvs_settings':
                            {
                                'VCLinkerTool':
                                {
                                    'SubSystem': 1,
                                    'OutputFile': '$(OutDir)\\fxfile-functional-tests_dbg.exe',
                                    'AdditionalLibraryDirectories': ['$(OutDir)'],
                                    'AdditionalDependencies': ['libxprw_dbg.lib', 'shell32.lib'],
                                },
                            },
                        },

                        'Release-x64-Unicode':
                        {
                            'inherit_from': ['Release-x64-Unicode_Base'],
                            'msvs_configuration_attributes':
                            {
                                'OutputDirectory': '../../bin/x64',
                                'IntermediateDirectory': '../../obj/fxfile-functional-tests/rel-x64',
                            },
                            'msvs_settings':
                            {
                                'VCLinkerTool':
                                {
                                    'SubSystem': 1,
                                    'OutputFile': '$(OutDir)\\fxfile-functional-tests.exe',
                                    'AdditionalLibraryDirectories': ['$(OutDir)'],
                                    'AdditionalDependencies': ['libxprw.lib', 'shell32.lib'],
                                },
                            },
                        },
                    },
                ],
            ],
        },
    },

    'targets':
    [
        {
            'target_name': 'fxfile-functional-tests',
            'type': 'executable',

            'dependencies':
            [
                '../xpr/xpr.gyp:xpr',
                '../fxfile-crash/fxfile-crash.gyp:fxfile-crash',
            ],

            'include_dirs':
            [
                '../xpr/include',
                '../fxfile',
                '../fxfile-crash',
                '../base',
            ],

            'sources':
            [
                'functional_tests.cpp',
                'functional_test_groups.h',
                'pattern_path_tests.cpp',
                'config_persistence_tests.cpp',
                'updater_contract_tests.cpp',
                '../fxfile/file_operation_core.cpp',
                '../fxfile/file_operation_core.h',
                '../fxfile/shell_registry_core.cpp',
                '../fxfile/shell_registry_core.h',
                '../fxfile/cmd/rename_transform_core.cpp',
                '../fxfile/cmd/rename_transform_core.h',
                '../base/crc32.c',
                '../base/crc32.h',
                '../base/md5.c',
                '../base/md5.h',
                '../base/hash-internal.h',
                '../base/fnmatch.cpp',
                '../base/fnmatch.h',
                '../base/conf_file.cpp',
                '../base/conf_file.h',
                '../base/conf_file_ex.h',
                '../base/version_compare.cpp',
                '../base/version_compare.h',
                '../base/upchecker_command.cpp',
                '../base/upchecker_command.h',
                '../base/update_metadata.h',
                '../base/update_download_limits.h',
            ],
        },
    ],
}
