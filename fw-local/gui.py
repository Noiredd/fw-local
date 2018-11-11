import datetime
import os

import tkinter as tk
from tkinter import ttk

import filters
from database import Database
from filmweb import FilmwebAPI
from plotting import drawHistogram
from presenter import Presenter

VERSION = '1.0-alpha.5'

class Login(object):
  # By default a dormant window that offers a request function to be called by
  # the API. That function blocks until user enters data and clicks to log in.
  # It then calls API again to do the actual backend login stuff.
  default_message = 'Zaloguj się do filmweb.pl'

  def __init__(self, root):
    self.__construct()
    self.session = None
    self.username = ''
    self.root = root
    self.window.resizable(0,0)
    self.window.attributes("-topmost", True)
    self.window.title('Zaloguj się')
    self.isDone = tk.BooleanVar()
    self.isDone.set(False)
    self.stateGood = True

  #PUBLIC
  def requestLogin(self, username:str=''):
    #bring up the window and block until user completes
    self.window.deiconify()
    #if the username was given by caller, prevent user from changing it
    self.username = username
    if username:
      #because there is no set() method :|
      self.usernameEntry.delete(0, 1000)
      self.usernameEntry.insert(0, username)
      self.usernameEntry.config(state=tk.DISABLED)
      self.passwordEntry.focus_set()
    else:
      self.usernameEntry.config(state=tk.NORMAL)
      self.usernameEntry.focus_set()
    self.root.wait_variable(self.isDone)
    _ses = self.session
    self.session = None
    self.isDone.set(False)
    #return both the acquired session as well as the (perhaps acquired) username
    return _ses, self.username

  #CONSTRUCTION
  def __construct(self):
    self.window = cw = tk.Toplevel()
    self.messageLabel = tk.Label(master=cw, text=self.default_message)
    self.messageLabel.grid(row=0, column=0, columnspan=2)
    tk.Label(master=cw, text='Nazwa użytkownika:').grid(row=1, column=0, sticky=tk.E)
    tk.Label(master=cw, text='Hasło:').grid(row=2, column=0, sticky=tk.E)
    self.usernameEntry = tk.Entry(master=cw, width=20)
    self.usernameEntry.grid(row=1, column=1, sticky=tk.W)
    self.usernameEntry.bind('<Key>', self._setStateGood)
    self.passwordEntry = tk.Entry(master=cw, width=20, show='*')
    self.passwordEntry.grid(row=2, column=1, sticky=tk.W)
    self.passwordEntry.bind('<Key>', self._setStateGood)
    self.infoLabel = tk.Label(master=cw, text='')
    self.infoLabel.grid(row=3, column=0, columnspan=2)
    tk.Button(master=cw, text='Zaloguj', command=self._loginClick).grid(row=4, column=1, sticky=tk.W)
    tk.Button(master=cw, text='Anuluj', command=self._cancelClick).grid(row=4, column=0, sticky=tk.E)
    self.window.withdraw()

  #CALLBACKS
  def _setStateBad(self, event=None):
    self.infoLabel['text'] = 'Niepowodzenie logowania!'
    self.stateGood = False
  def _setStateGood(self, event=None):
    if not self.stateGood:
      self.infoLabel['text'] = ''
      self.stateGood = True
    #also, maybe the user has hit enter key, meaning to log in
    if event.keycode == 13:
      self._loginClick()
  def _loginClick(self):
    #collect login data
    username = self.usernameEntry.get()
    password = self.passwordEntry.get()
    self.passwordEntry.delete(0, tk.END)  #always clear the password field
    #attempt to log in
    session = FilmwebAPI.login(username, password)
    if session is None:
      self._setStateBad()
    else:
      #clear&hide, store session/username and pass control back to the caller
      self.usernameEntry.delete(0, tk.END)
      self.session = session
      self.username = username
      self.isDone.set(True)
      self.window.withdraw()
  def _cancelClick(self):
    self.passwordEntry.delete(0, tk.END)
    self.usernameEntry.delete(0, tk.END)
    self.session = None
    self.isDone.set(True)
    self.window.withdraw()

class Detail(object):
  default_font  = 'TkDefaultFont'
  font_title    = (default_font, 24)
  font_otitle   = (default_font, 10)
  font_rating   = (default_font, 48)
  font_fwRating = (default_font, 20)
  font_favorite = (default_font, 32)
  font_comment  = (default_font, 12, 'italic')
  favorite_sign = '♥'

  def __init__(self, root):
    self.__construct()
    self.root = root
    self.window.resizable(0,0)
    self.window.title('Podgląd')

  #PUBLIC
  def launchPreview(self, item):
    #fill the window with item's data and bring it up
    self.titleLabel['text']    = item['title']
    self.otitleLabel['text']   = item['otitle']
    self.yearLabel['text']     = item['year']
    self.genreLabel['text']    = ', '.join(item['genres'])
    #TODO: this nasty hack could be avoided by reworking database & blueprint
    #so that movies are stored as objects instead of as dicts/lists
    #(this would allow item.getDuration() instead of that)
    self.durationLabel['text'] = Blueprint['duration']['presentation']['format'](item['duration'])
    self.countryLabel['text']  = ', '.join(item['countries'])
    self.directorLabel['text'] = ', '.join(item['directors'])
    self.castLabel['text']     = ', '.join(item['cast'])
    self.fwRatingLabel['text'] = '{:.2f}'.format(float(item['fwRating']))
    self.ratingLabel['text']   = item['rating'] if item['rating'] != '0' else '-'
    #TODO: same here
    self.favoriteHeart['text'] = Blueprint['favourite']['presentation']['format'](item['favourite'])
    self.timeSeenLabel['text'] = str(item['timeSeen'])
    self.commentLabel['text']  = Blueprint['comment']['presentation']['format'](item['comment'])
    self.window.title(self._makeTitle(item))
    self.window.deiconify()

  #CONSTRUCTION
  def __construct(self):
    self.window = cw = tk.Toplevel()
    self.posterLabel = tk.Label(master=cw, text='POSTER', width=15, height=10, anchor=tk.NW)
    self.posterLabel.grid(row=0, column=0, rowspan=3)
    ti = tk.Frame(cw) #title frame
    self.titleLabel = tk.Label(master=ti, text='', width=30, anchor=tk.NW, font=self.font_title)
    self.titleLabel.grid(row=0, column=0, sticky=tk.NW)
    self.otitleLabel = tk.Label(master=ti, text='', anchor=tk.NW, font=self.font_otitle)
    self.otitleLabel.grid(row=1, column=0, sticky=tk.NW)
    mi = tk.Frame(cw) #main info frame
    self.yearLabel = tk.Label(master=mi, text='', width=7, anchor=tk.NW)
    self.yearLabel.grid(row=0, column=0, sticky=tk.NW, padx=5)
    self.countryLabel = tk.Label(master=mi, text='', width=30, anchor=tk.N)
    self.countryLabel.grid(row=0, column=1, sticky=tk.NW)
    self.genreLabel = tk.Label(master=mi, text='', width=35, anchor=tk.N)
    self.genreLabel.grid(row=0, column=2, sticky=tk.NW)
    self.durationLabel = tk.Label(master=mi, text='', width=7, anchor=tk.NE)
    self.durationLabel.grid(row=0, column=3, sticky=tk.NW, padx=5)
    di = tk.Frame(cw) #detailed info frame
    tk.Label(master=di, text='Reżyser:', anchor=tk.NW).grid(row=1, column=0, sticky=tk.NW)
    self.directorLabel = tk.Label(master=di, text='', width=25, anchor=tk.NW)
    self.directorLabel.grid(row=1, column=1, sticky=tk.NW)
    tk.Label(master=di, text='Obsada:', anchor=tk.NW).grid(row=2, column=0, sticky=tk.NW)
    self.castLabel = tk.Label(master=di, text='', width=40, anchor=tk.NW)
    self.castLabel.grid(row=2, column=1, sticky=tk.NW)
    fi = tk.Frame(cw) #filweb rating frame
    tk.Label(master=fi, text='Ocena\nFilmwebu:', anchor=tk.NW, justify=tk.LEFT).grid(row=0, column=0, stick=tk.SE)
    self.fwRatingLabel = tk.Label(master=fi, text='', font=self.font_fwRating)
    self.fwRatingLabel.grid(row=0, column=1, sticky=tk.SE)
    ri = tk.Frame(cw) #rating info frame
    self.ratingLabel = tk.Label(master=ri, text='', width=2, font=self.font_rating)
    self.ratingLabel.grid(row=0, column=0)
    self.favoriteHeart = tk.Label(master=ri, text='', width=1, font=self.font_favorite)
    self.favoriteHeart.grid(row=0, column=1)
    self.timeSeenLabel = tk.Label(master=ri, text='')
    self.timeSeenLabel.grid(row=1, column=0, columnspan=2)
    self.commentLabel = tk.Label(master=ri, text='', width=55, wraplength=450, anchor=tk.CENTER, font=self.font_comment)
    self.commentLabel.grid(row=0, column=2, rowspan=2, sticky=tk.W)
    #put the window together
    ti.grid(row=0, column=1, columnspan=2, sticky=tk.NW)
    mi.grid(row=1, column=1, columnspan=2, sticky=tk.NW)
    di.grid(row=2, column=1, sticky=tk.NW)
    fi.grid(row=2, column=2, sticky=tk.NE)
    ri.grid(row=3, column=1, columnspan=2, sticky=tk.NW)
    tk.Button(master=cw, text='Zamknij', command=self._closeClick).grid(row=4, column=2, sticky=tk.SE)
    self.window.withdraw()

  #CALLBACKS
  def _closeClick(self):
    self.window.withdraw()

  #INTERNALS
  def _makeTitle(self, item):
    return '{} ({})'.format(item['title'], item['year'])

class Main(object):
  filename = 'userdata.fws' # TODO: maybe use user's local folder?

  def __init__(self):
    self.root = root = tk.Tk()
    #prepare the components
    self.loginHandler = Login(self.root)
    self.detailHandler = Detail(self.root)
    #prepare the window
    root.title('FW local')
    root.resizable(0,0)
    self.__construct()
    #load the savefile and instantiate Presenter(s) and Database(s)
    userdata = self.loadUserData()
    u_name = userdata[1] if userdata else ''
    conf_m = userdata[2] if userdata else ''
    data_m = userdata[3] if userdata else ''
    self.api = FilmwebAPI(self.loginHandler.requestLogin, u_name)
    self.database = Database.restoreFromString('Movie', data_m, self.api, self._setProgress)
    self.presenter = Presenter(root, self.api, self.database, conf_m)
    self.presenter.grid(row=0, column=0, rowspan=3, columnspan=3, padx=5, pady=5, sticky=tk.NW)
    self.presenter.addFilter(filters.YearFilter, row=0, column=0, sticky=tk.NW)
    self.presenter.addFilter(filters.RatingFilter, row=1, column=0, sticky=tk.NW)
    self.presenter.addFilter(filters.DateFilter, row=2, column=0, sticky=tk.NW)
    self.presenter.addFilter(filters.GenreFilter, row=0, column=1, rowspan=3, sticky=tk.NW)
    self.presenter.addFilter(filters.CountryFilter, row=0, column=2, rowspan=3, sticky=tk.NW)
    self.presenter.addFilter(filters.DirectorFilter, row=0, column=3, rowspan=3, sticky=tk.NW)
    self.presenter.totalUpdate()
    #center window AFTER creating everything (including plot)
    self.centerWindow()
    #ensure a controlled exit no matter what user does (X-button, alt+f4)
    root.protocol('WM_DELETE_WINDOW', self._quit)
    if not userdata:
      self._reloadData() # first run
    tk.mainloop()

  #CONSTRUCTION
  def __construct(self):
    #control panel
    frame = tk.Frame(self.root)
    tk.Button(frame, text='Aktualizuj', command=self._updateData).grid(row=0, column=0, sticky=tk.SW)
    tk.Button(frame, text='PRZEŁADUJ!', command=self._reloadData).grid(row=0, column=1, sticky=tk.SW)
    self.progressVar = tk.IntVar()
    self.progressbar = ttk.Progressbar(self.root, orient='horizontal', length=400, mode='determinate', variable=self.progressVar)
    self.progressbar.grid(row=4, column=1, padx=5, pady=5)
    self._setProgress(-1) # start with the progress bar hidden
    tk.Button(self.root, text='Wyjście', command=self._quit).grid(row=4, column=2, padx=5, pady=5, sticky=tk.SE)
    frame.grid(row=4, column=0, padx=5, pady=5, sticky=tk.S+tk.W)
  def centerWindow(self):
    self.root.update()
    ws = self.root.winfo_screenwidth()
    hs = self.root.winfo_screenheight()
    w = self.root.winfo_width()
    h = self.root.winfo_height()
    x = ws/2 - w/2
    y = hs/2 - h/2
    self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))

  #USER DATA MANAGEMENT
  def loadUserData(self):
    # loads data and returns it as list of lines - for format, see saveUserData
    if not os.path.exists(self.filename):
      return None
    with open(self.filename, 'r') as userfile:
      userdata = [line.strip('\n') for line in userfile.readlines() if not line.startswith('#')]
    return userdata
  def saveUserData(self):
    # if for any reason the first update hasn't commenced - don't save anything
    if self.api.username is None:
      return
    # safety feature against failing to write new data and removing the old
    if os.path.exists(self.filename):
      os.rename(self.filename, self.filename + '.bak')
    with open(self.filename, 'w') as userfile:
      userfile.write('#VERSION\n')
      userfile.write(VERSION + '\n')
      userfile.write('#USERNAME\n')
      userfile.write(self.api.username + '\n')
      userfile.write('#MOVIES\n')
      userfile.write(self.presenter.storeToString() + '\n')
      userfile.write(self.database.storeToString() + '\n')
      # series and games can be added sequentially right after
    # if there were no errors at point, new data has been successfully written
    if os.path.exists(self.filename + '.bak'):
      os.remove(self.filename + '.bak')

  #CALLBACKS
  def _spawnPreview(self, event=None):
    #this is only effective is the user double-clicks a Treeview's cell
    if event is not None:
      region = self.tree.identify_region(event.x, event.y)
      if region=='cell':
        itemID = self.tree.identify_row(event.y)
        item = self.tree.item(itemID)
        itemID = item['values'][0]
        movie = self.database.getMovieByID(itemID)
        #if the user clicked on a movie, display the detailed view
        if movie is not None:
          self.detailHandler.launchPreview(movie)
  def _setProgress(self, value:int):
    # allows the caller to set the percentage value of the progress bar
    # non-negative values cause the bar to show up, negative hides it
    if value < 0:
      self.progressbar.grid_remove()
      self.progressVar.set(0)
    else:
      self.progressbar.grid()
      self.progressVar.set(value)
    self.root.update()
  def _updateData(self):
    # call softUpdate on (all) the database(s)
    self.database.softUpdate()
    # update (all) the presenter(s)
    self.presenter.totalUpdate()
    # save data
    self.saveUserData()
  def _reloadData(self):
    self.database.hardUpdate()
    self.presenter.totalUpdate()
    self.saveUserData()
  def _quit(self):
    self.saveUserData()
    self.root.quit()

Main()
