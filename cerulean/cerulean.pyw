import wx
import wx.adv
import requests
import pickle

class MainFrame(wx.Frame):
    """ We simply derive a new class of Frame. """
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(200,100), name=title)
        self.Bind(wx.EVT_CLOSE, self.onClose)

        try:
            conf = pickle.load(open("conf.dat", "rb"))
        except FileNotFoundError:
            conf = {"usernames": [], "interval": 10}
            pickle.dump(conf, open("conf.dat", "xb"))
        except FileExistsError:
            # what the hell
            assert False, "Dear user, you should never have to see this. If you see it, consider yourself lucky, as this message is impossible to see and you must've broken spacetime itself to see it. I bow down to you."
        
        self.icon = wx.Icon(name="map.png", type=wx.BITMAP_TYPE_PNG)
        self.SetIcon(self.icon)
        self.taskbarIcon = wx.adv.TaskBarIcon()
        self.taskbarIcon.SetIcon(self.icon)

        mainPanel = wx.Panel(self)

        self.targetLabel = wx.StaticText(mainPanel, label="Target BlueMap server (as URL)", pos=(0, 0))
        self.targetEntry = wx.TextCtrl(mainPanel, pos=(0, 20))
        self.targetButton = wx.Button(mainPanel, label = "Connect", pos=(self.targetEntry.Size.width + 5, 15))
        
        self.connectNotif = wx.adv.NotificationMessage(
            "Connecting",
            message="Cerulean is connecting to the target server...",
            parent=self)
        self.connectNotif.UseTaskBarIcon(self.taskbarIcon)
        
        self.Show(True)
        
    def onClose(self, event):
        self.taskbarIcon.Destroy()
        self.Destroy()

app = wx.App(False)
frame = MainFrame(None, 'Cerulean')
app.MainLoop()
