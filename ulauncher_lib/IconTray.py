from gi.repository import Gtk


class IconoTray:
    def __init__(self, iconname):
        self.menu = Gtk.Menu()

        self.__app_ind_support = 1

        try:
            from gi.repository import AppIndicator3
        except:
            self.__app_ind_support = 0

        if self.__app_ind_support == 1:
            self.ind = AppIndicator3.Indicator.new(iconname, "", AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            self.ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.ind.set_menu(self.menu)
        else:
            self.my_status_icon = Gtk.StatusIcon()
            self.my_status_icon.connect('popup-menu', self.right_click_event_statusicon)

    def set_icon(self, path):

        if self.__app_ind_support == 1:
            self.ind.set_icon(path)
        else:
            self.my_status_icon.set_from_icon_name(path)

    def add_menu_item(self, command, title):

        menu_item = Gtk.MenuItem()
        menu_item.set_label(title)
        menu_item.connect("activate", command)

        self.menu.append(menu_item)
        self.menu.show_all()

    def add_seperator(self):

        menu_item = Gtk.SeparatorMenuItem()
        self.menu.append(menu_item)
        self.menu.show_all()

    def get_tray_menu(self):
        return self.menu

    def right_click_event_statusicon(self, icon, button, time):

        self.get_tray_menu()

        def pos(menu, aicon):
            return (Gtk.StatusIcon.position_menu(menu, aicon))

        self.menu.popup(None, None, pos, icon, button, time)