import wx
import wx.adv
import requests
import pickle
from copy import copy

class ButtonEntry():
    def __init__(self, parent, clickedHandler, pos, buttonLabel, margin = 10, content = ""):
        self.handler = clickedHandler
        self.entry = wx.TextCtrl(parent, pos=pos)
        self.entry.write(content)
        self.button = wx.Button(parent, label = buttonLabel, pos=(self.entry.Size.width + margin, self.entry.Position.y))
        self.button.Bind(wx.EVT_BUTTON, self._handler)
    def _handler(self, *args, **kwargs):
        self.handler(self.entry.GetLineText(0), *args, **kwargs)

class CeruleanTaskBarIcon(wx.adv.TaskBarIcon):
    TBMENU_CLOSE = wx.NewIdRef()
    
    def __init__(self, parent):
        wx.adv.TaskBarIcon.__init__(self)
        self.parent = parent
        
        self.SetIcon(parent.icon)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_UP, lambda x: parent.Show())
        self.Bind(wx.EVT_MENU, lambda x: wx.CallAfter(parent.close), id=self.TBMENU_CLOSE)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.TBMENU_CLOSE, "Close Cerulean")
        return menu

class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(270,320), name=title)
        self.Bind(wx.EVT_CLOSE, lambda x: self.Hide())
        self.connected = False
        self.active = True
        self.playerData = None
        try:
            self.conf = pickle.load(open("conf.dat", "rb"))
        except FileNotFoundError:
            self.conf = {"url": "", "usernames": [], "interval": 10}
            pickle.dump(self.conf, open("conf.dat", "xb"))
        except FileExistsError:
            # what the hell
            assert False, "Dear user, you should never have to see this. If you see it, consider yourself lucky, as this message is impossible to see and you must've broken spacetime itself to see it. I bow down to you."
        
        self.icon = wx.Icon(name="map.png", type=wx.BITMAP_TYPE_PNG)
        self.SetIcon(self.icon)
        self.taskbarIcon = CeruleanTaskBarIcon(parent=self)

        mainPanel = wx.Panel(self)
        self.bar = self.CreateStatusBar(number = 2)
        self.bar.SetStatusWidths([-3, -1])
        self.bar.PushStatusText("Disconnected")
        self.bar.PushStatusText("", field = 1)

        self.targetLabel = wx.StaticText(mainPanel, label="Target BlueMap server (as URL)", pos=(5, 5))
        self.targetEntry = ButtonEntry(mainPanel, self.connectToServer, (5, 25), "Connect", content = self.conf["url"])
        self.playersLabel = wx.StaticText(mainPanel, label="Players to watch", pos=(5, 75))
        self.playersListBox = wx.ListBox(mainPanel, size = (150, 125), pos=(5, 100))
        self.playersAddButton = wx.Button(mainPanel, label = "Add", pos=(157, 100))
        self.playersAddButton.Bind(wx.EVT_BUTTON, self.addPlayer)
        self.playersRemoveButton = wx.Button(mainPanel, label = "Remove", pos=(157, 140))
        self.playersRemoveButton.Bind(wx.EVT_BUTTON, self.removePlayer)
        #self.playersDetailsButton = wx.Button(mainPanel, label = "Details", pos=(157, 135))
        self.playersListBox.InsertItems(self.conf["usernames"], 0) if len(self.conf["usernames"]) else 0
        if not len(self.conf["usernames"]):
            self.playersRemoveButton.Disable()
            #self.playersDetailsButton.Disable()
        else:
            self.playersListBox.SetSelection(0)
        def text(evt):
            print(dir(evt))
        self.playersListBox.Bind(wx.EVT_LISTBOX, text)
        self.enabledButton = wx.ToggleButton(mainPanel, label="Disconnected", pos=(5, 230))
        self.enabledButton.Bind(wx.EVT_TOGGLEBUTTON, self.setEnabled)
        self.enabledButton.Disable()

        self.statusTimer = wx.Timer(self, 0)
        self.Bind(wx.EVT_TIMER, self.onTimer)
        self.statusTimer.Start(self.conf["interval"]*1000)
        
        self.connectNotif = wx.adv.NotificationMessage(
            "Connecting",
            message="Cerulean is connecting to the target server... (The application may freeze for a short time, this is normal).",
            parent=self)
        self.connectNotif.UseTaskBarIcon(self.taskbarIcon)
        self.connectedNotif = wx.adv.NotificationMessage(
            "Connected to target",
            message="Cerulean has connected to the target successfully!",
            parent=self)
        self.connectedNotif.UseTaskBarIcon(self.taskbarIcon)
        self.errorNotif = wx.adv.NotificationMessage(
            "Failed to get data",
            message="Cerulean was unable to retrieve player data from the target!",
            flags = wx.ICON_ERROR,
            parent=self)
        self.errorNotif.UseTaskBarIcon(self.taskbarIcon)
        
        self.Show(True)
        
    def connectToServer(self, url, event):
        if self.targetEntry.button.GetLabel() == "Disconnect":
            self.disconnectFromServer()
            return
        self.bar.PushStatusText("Connecting")
        self.connectNotif.Show(self.connectNotif.Timeout_Never)
        try:
            requests.get(url+"/live/players")
        except requests.exceptions.ConnectionError as e:
            self.bar.PushStatusText("Disconnected")
            error = wx.MessageDialog(self, "Error while connecting to target \"" + url + "\": " + str(e) + "\nCheck that you're using the correct schema (i.e. http instead of https) and that you didn't mostype the url.", caption = "Error connecting to target! Is the URL correct?", style=wx.OK|wx.ICON_ERROR|wx.CENTRE)
            error.ShowModal()
            self.connectNotif.Close()
        except requests.exceptions.MissingSchema:
            self.bar.PushStatusText("Disconnected")
            error = wx.MessageDialog(self, "Error connecting to target! You forgot to include the http(s):// part of the url.", caption = "Error while connecting to target \"" + url + "\"", style=wx.OK|wx.ICON_ERROR|wx.CENTRE)
            error.ShowModal()
            self.connectNotif.Close()
        else:
            self.conf["url"] = url
            self.connected = True
            self.playerData = requests.get(self.conf["url"]+"/live/players").json()
            self.connectNotif.Close()
            self.connectedNotif.Show()
            self.bar.PushStatusText("Connected to target " + url)
            self.bar.PushStatusText("Idle", field = 1)
            self.enabledButton.Enable()
            self.enabledButton.SetValue(True)
            self.enabledButton.SetLabel("Stop scanning")
            self.targetEntry.button.SetLabel("Disconnect")
    def disconnectFromServer(self):
        self.connected = False
        self.enabledButton.Disable()
        self.enabledButton.SetLabel("Disconnected")
        self.enabledButton.SetValue(False)
        self.targetEntry.button.SetLabel("Connect")
        self.bar.PushStatusText("Disconnected")
        self.bar.PushStatusText("", field = 1)
    def checkPlayerStatus(self):
        if self.connected and self.active:
            self.bar.PushStatusText("Checking", field = 1)
            try:
                _playerData = requests.get(self.conf["url"]+"/live/players").json()
            except Exception:
                self.errorNotif.Show()
            else:
                for counter, itm in enumerate(self.playersListBox.GetItems()):
                    item = copy(itm)
                    item = (" ".join(item.split()[:-1])) if len(item.split()) != 1 else item
                    if item in [item["name"] for item in _playerData["players"]] and item not in [item["name"] for item in self.playerData["players"]]:
                        self.playersListBox.SetString(counter, item + " [ONLINE]")
                        playerNotif = wx.adv.NotificationMessage(
                            "Player online!",
                            message="Player \"" + item + "\" is online!",
                            parent=self)
                        playerNotif.Show()
                    elif item not in [item["name"] for item in _playerData["players"]] and item in [item["name"] for item in self.playerData["players"]]:
                        self.playersListBox.SetString(counter, item)
                self.playerData = _playerData
                self.bar.PushStatusText("Idle", field = 1)
                
    def addPlayer(self, event):
        dialog = wx.TextEntryDialog(self, "Please enter the EXACT username of the player you wish to watch.", "Enter username")
        dialog.ShowModal()
        if dialog.GetValue() != "":
            self.playersListBox.InsertItems([dialog.GetValue()], 0)
            self.conf["usernames"] = self.playersListBox.GetItems()
            self.playersRemoveButton.Enable()
    def removePlayer(self, event):
        self.playersListBox.Delete(self.playersListBox.GetSelection())
        self.conf["usernames"] = self.playersListBox.GetItems()
        if not len(self.conf["usernames"]):
            self.playersRemoveButton.Disable()

    def setEnabled(self, event):
        self.active = self.enabledButton.GetValue()
        if self.enabledButton.GetValue():
            self.enabledButton.SetLabel("Stop scanning")
        else:
            self.enabledButton.SetLabel("Start scanning")
    
    def onTimer(self, event):
        if event.Id == 0:
            self.checkPlayerStatus()
    
    def close(self):
        pickle.dump(self.conf, open("conf.dat", "wb"))
        self.taskbarIcon.Destroy()
        self.Destroy()

app = wx.App(False)
frame = MainFrame(None, 'Cerulean')
app.MainLoop()
