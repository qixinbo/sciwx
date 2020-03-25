import sys, wx
sys.path.append('../../')
from skimage.draw import line, circle
from sciwx.canvas import CanvasFrame
from sciwx.action import Tool, DefaultTool
from sciwx.app.manager import App

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
    
    def mouse_up(self, ips, x, y, btn, **key):
        self.status = False
    
    def mouse_move(self, ips, x, y, btn, **key):
        if not self.status:return

        value = (255, 0, 0)
        w = self.para['width']
        drawline(ips.img, self.oldp, (y, x), w, value)
        self.oldp = (y, x)
        key['canvas'].update()
        
    def mouse_wheel(self, ips, x, y, d, **key):pass

class TestFrame(CanvasFrame, App):
    def __init__ (self, parent):
        CanvasFrame.__init__(self, parent)
        App.__init__(self)

        self.Bind(wx.EVT_ACTIVATE, self.init_image)
        
    def init_image(self, event):
        self.add_img(self.canvas.image)

if __name__=='__main__':
    from skimage.data import camera, astronaut
    from skimage.io import imread

    app = wx.App()
    cf = TestFrame(None)
    cf.set_img(astronaut())
    cf.set_cn((0,1,2))
    bar = cf.add_toolbar()
    bar.add_tool('M', DefaultTool)
    bar.add_tool('P', Pencil)
    cf.Show()
    app.MainLoop()
