# coding=utf8

# ===== nvil_houdini_applink.py
#
# Copyright (c) 2017 Artur J. Żarek
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hou
import sys
import os
import time
import rpyc


def export_from_houdini():
    selection = hou.selectedNodes()
    if len(selection) > 1:
        hou.ui.displayMessage('Only first object will be exported.', severity=hou.severityType.Warning)
    elif len(selection) == 0:
        hou.ui.displayMessage('Nothing to export!', severity=hou.severityType.Error)
        sys.exit(1)

    if not isinstance(selection[0], hou.SopNode):
        hou.ui.displayMessage('Select a single SOP node.', severity=hou.severityType.Error)
        sys.exit(2)

    # Paths and files
    instructions_filename = 'NVil Instructions.txt'
    message_filename = 'NVil Message_In.txt'

    # First, save the selected SOP to NVil clipboard directory.
    selection[0].geometry().saveToFile(get_path()['clipboard_file_path'])

    # Then, save instructions for NVil.
    instructions = ['TID Common Modeling Shortcut Tools >> Clipboard Paste']
    abs_instructions_file_path = os.path.join(get_path()['nvil_appdata'], instructions_filename)
    with open(abs_instructions_file_path, 'w') as out:
        for instruction in instructions:
            out.write(instruction)

    # Finally, tell NVil to import the file.
    abs_message_file_path = os.path.join(get_path()['nvil_appdata'], message_filename)
    try:
        with open(abs_message_file_path, 'w') as out:
            out.write('Execute External Instruction File')
    except IOError:
        hou.ui.displayMessage('Target file locked.\n Switch to NVil and check if the import dialog is closed.',
                              severity=hou.severityType.Error)
        sys.exit(3)

    hou.ui.setStatusMessage('Done. You can now switch to NVil.', severity=hou.severityType.Message)


def export_from_nvil(port=18811):
    main_module = 'nvil_houdini.nvil_houdini_applink'
    try:
        conn = rpyc.classic.connect('localhost', port)
        conn.execute('import ' + main_module)
        conn.execute('reload(' + main_module + ')')
        conn.execute(main_module + '.load_geo()')
    except Exception:  # TODO: Too general.
        print("There were errors. Have you started Houdini's RPC server?")
        time.sleep(3)
        sys.exit(1)


def load_geo():
    selected_nodes = hou.selectedNodes()
    if len(selected_nodes) != 1:
        hou.ui.displayMessage('You need to select a single SOP node.', severity=hou.severityType.Error)
        sys.exit(2)
    selection = selected_nodes[0]

    if not isinstance(selection, hou.SopNode):
        hou.ui.displayMessage('Selected node must be a SOP.', severity=hou.severityType.Error)
        sys.exit(2)

    nvil_import = hou.node(selection.parent().path()).createNode('file')
    nvil_import.setFirstInput(selection)
    nvil_import.moveToGoodPosition()

    nvil_import.setParms({'file': get_path()['clipboard_file_path']})
    nvil_import.setDisplayFlag(True)
    selection.setRenderFlag(False)
    nvil_import.setHardLocked(True)
    nvil_import.setSelected(True, clear_all_selected=True)


def get_path():
    appdata_path = hou.getenv('APPDATA')
    nvil_appdata = os.path.join(appdata_path, 'DigitalFossils', 'NVil')
    clipboard_file_path = os.path.join(nvil_appdata, 'Media', 'Clipboard', 'ClipboardObj.obj')
    return {'nvil_appdata': nvil_appdata, 'clipboard_file_path': clipboard_file_path}


if __name__ == '__main__':
    export_from_nvil()