import sys, wx
sys.path.append('../../')

from sciwx.mark.mark import GeometryMark 

mark =  {'type': 'layer', 'body': [{'type': 'rectangle', 'body': (117, 133, 96, 96), 'color': (255, 0, 128)}, {'type': 'circle', 'body': (117, 133, 2), 'color': (255, 0, 128)}, {'type': 'text', 'body': (69, 85, 'S:30 W:48'), 'pt': False, 'color': (255, 0, 128)}]}
geometry_mark = GeometryMark(mark)

def f(x, y):
    return x, y

class Example(wx.Frame):

    def __init__(self, *args, **kw):
        super(Example, self).__init__(*args, **kw)

        self.Bind(wx.EVT_PAINT, self.DrawMarks)

    def DrawMarks(self, e):
        dc = wx.ClientDC(self)
        geometry_mark.draw(dc, f, k=1)

app = wx.App()
ex = Example(None)
ex.Show()
app.MainLoop()
