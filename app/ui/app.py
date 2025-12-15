import customtkinter as ctk

from app.config import APP_TITLE, WINDOW_SIZE, BG_COLOR
from app.views.login import LoginPage
from app.ui.admin_pages import AdminHomePage
from app.ui.adopter_pages import AdopterHomePage


class App(ctk.CTk):
    """
    Root application window that wires up views and handles navigation.
    """

    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        # Start maximized; still allow resizing. Fallback to full screen dimensions if zoom is unsupported.
        try:
            self.state("zoomed")
        except Exception:
            pass
        try:
            # Ensure at least full screen size even if zoom didn't stick
            self.update_idletasks()
            w, h = self.winfo_screenwidth(), self.winfo_screenheight()
            self.geometry(f"{w}x{h}+0+0")
        except Exception:
            self.geometry(WINDOW_SIZE)
        self.resizable(True, True)
        self.configure(fg_color=BG_COLOR)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.current_user = None
        self.container = ctk.CTkFrame(self, fg_color="#D4FAFF")
        self.container.pack(fill="both", expand=True)

        self.pages = {}
        self.build_pages()
        self.show_page("login")

    def build_pages(self):
        self.pages["login"] = LoginPage(self.container, self)
        self.pages["admin_home"] = AdminHomePage(self.container, self)
        self.pages["adopter_home"] = AdopterHomePage(self.container, self)

    def show_page(self, name: str):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[name].pack(fill="both", expand=True)

    def handle_login(self, role_key: str, user):
        """
        Called by the LoginPage after successful auth. Rebuild home view for the role.
        """
        self.current_user = user

        if role_key == "admin":
            if "admin_home" in self.pages:
                try:
                    self.pages["admin_home"].destroy()
                except Exception:
                    pass
            self.pages["admin_home"] = AdminHomePage(self.container, self)
            self.show_page("admin_home")
        else:
            if "adopter_home" in self.pages:
                try:
                    self.pages["adopter_home"].destroy()
                except Exception:
                    pass
            self.pages["adopter_home"] = AdopterHomePage(self.container, self)
            self.show_page("adopter_home")

    def logout(self):
        self.current_user = None
        self.show_page("login")


def run_app():
    app = App()
    app.mainloop()
