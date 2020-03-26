import sys, wx
sys.path.append('../../')

from sciwx.action import Tool
from sciwx.manager import ColorManager
from sciwx.canvas import CanvasFrame
from sciwx.app.manager import App

from skimage.data import astronaut
from skimage.draw import line, circle

class ColorPicker(Tool):
    """ColorPicker class plugin with events callbacks"""
    title = 'Color Picker'
    para = {'front':(255,255,255), 'back':(0,0,0)}
    view = [('color', 'front', 'front', 'color'),
            ('color', 'back', 'back', 'color')]
        
    def config(self):
        ColorManager.set_front(self.para['front'])
        ColorManager.set_back(self.para['back'])
        
    def mouse_down(self, ips, x, y, btn, **key):
        if btn == 1:ColorManager.set_front(ips.img[int(y), int(x)])
        if btn == 3:ColorManager.set_back(ips.img[int(y), int(x)])
        print(ips.img[int(y), int(x)])
        print(ColorManager.get_front())
    
    def mouse_up(self, ips, x, y, btn, **key):
        pass
    
    def mouse_move(self, ips, x, y, btn, **key):
        pass
        
    def mouse_wheel(self, ips, x, y, d, **key):
        pass

def drawline(img, oldp, newp, w, value):
    if img.ndim == 2: value = sum(value)/3
    oy, ox = line(*[int(round(i)) for i in oldp+newp])
    cy, cx = circle(0, 0, w/2+1e-6)
    ys = (oy.reshape((-1,1))+cy).clip(0, img.shape[0]-1)
    xs = (ox.reshape((-1,1))+cx).clip(0, img.shape[1]-1)
    img[ys.ravel(), xs.ravel()] = value

class Pencil(Tool):
    title = 'Pencil'
    
    para = {'width':1}
    view = [(int, 'width', (0,30), 0,  'width', 'pix')]
    
    def __init__(self):
        self.status = False
        self.oldp = (0,0)
        
    def mouse_down(self, ips, x, y, btn, **key):
        self.status = True
        self.oldp = (y, x)
        ips.snapshot()
    
    def mouse_up(self, ips, x, y, btn, **key):
        self.status = False
    
    def mouse_move(self, ips, x, y, btn, **key):
        if not self.status:return
        w = self.para['width']
        value = ColorManager.get_front()
        drawline(ips.img, self.oldp, (y, x), w, value)
        self.oldp = (y, x)
        ips.update()
        
    def mouse_wheel(self, ips, x, y, d, **key):pass


class TestFrame(CanvasFrame, App):
    def __init__ (self, parent):
        CanvasFrame.__init__(self, parent)
        App.__init__(self)

        self.Bind(wx.EVT_ACTIVATE, self.init_image)
        
    def init_image(self, event):
        self.add_img(self.canvas.image)

if __name__ == '__main__':
    app = wx.App()
    cf = TestFrame(None)
    cf.set_img(astronaut())
    cf.set_cn((0,1,2))
    bar = cf.add_toolbar()
    bar.add_tool('C', ColorPicker)
    bar.add_tool('P', Pencil)
    bar.add_tool('U', Undo)
    cf.Show()
    app.MainLoop()