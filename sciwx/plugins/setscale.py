from sciwx.action import Tool
from sciwx.widgets import ParaDialog
from sciwx.manager import ConfigManager

class SetScale(Tool):
    """ColorPicker class plugin with events callbacks"""
    title = 'Set Scale'
    
    def __init__(self):
        self.pos = []

    def mouse_down(self, ips, x, y, btn, **key):
        self.pos.append((y, x))
    
    def mouse_up(self, ips, x, y, btn, **key):
        if len(self.pos) == 2:
            print("pos = ", self.pos)
            para = {'scalebar': 200}
            view = [('lab', 'lab', 'Please input the real length the scale bar'),
            (int, 'scalebar', (0, 1000), 1, 'Length', 'um')]
            pd = ParaDialog(None, 'Scale bar')
            pd.init_view(view, para, preview=False, modal=True)
            pd.ShowModal()
            ConfigManager.set('scalebar', para['scalebar']/(self.pos[1][1]-self.pos[0][1]))
            print(ConfigManager.get('scalebar'))

    
    def mouse_move(self, ips, x, y, btn, **key):
        pass
        
    def mouse_wheel(self, ips, x, y, d, **key):
        pass