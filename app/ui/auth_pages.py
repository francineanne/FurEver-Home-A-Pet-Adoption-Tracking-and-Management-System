# auth_pages.py
import customtkinter as ctk
from tkinter import messagebox

from app.controllers import AuthController


class LoginPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.auth = AuthController()

        self.pack(fill="both", expand=True)
        self.configure(fg_color="white")

        # -----------------------------
        # TITLE
        # -----------------------------
        ctk.CTkLabel(
            self,
            text="FurEver Home",
            font=("Arial Black", 24)
        ).pack(pady=20)

        # -----------------------------
        # EMAIL
        # -----------------------------
        ctk.CTkLabel(self, text="Email:", anchor="w").pack(pady=(10, 0))
        self.email_entry = ctk.CTkEntry(self, width=300)
        self.email_entry.pack()

        # -----------------------------
        # PASSWORD
        # -----------------------------
        ctk.CTkLabel(self, text="Password:", anchor="w").pack(pady=(10, 0))
        self.password_entry = ctk.CTkEntry(self, width=300, show="*")
        self.password_entry.pack()

        # -----------------------------
        # ROLE DROPDOWN
        # -----------------------------
        ctk.CTkLabel(self, text="Login as:", anchor="w").pack(pady=(10, 0))
        self.role_menu = ctk.CTkComboBox(
            self, width=300,
            values=["adopter", "admin"]
        )
        self.role_menu.set("adopter")
        self.role_menu.pack()

        # -----------------------------
        # LOGIN BUTTON
        # -----------------------------
        ctk.CTkButton(
            self,
            text="Login",
            width=300,
            command=self.try_login
        ).pack(pady=30)

    # ------------------------------------------------
    # LOGIN LOGIC (delegated to controller)
    # ------------------------------------------------
    def try_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_menu.get().strip()

        if not email or not password:
            messagebox.showerror("Error", "Email and password required.")
            return

        role_key = "admin" if role.lower().startswith("admin") else "adopter"
        try:
            user = self.auth.login(email, password, role_key)
        except ValueError as e:
            messagebox.showerror("Login Failed", str(e))
            return
        except Exception as e:
            messagebox.showerror("Login Failed", f"Unexpected error: {e}")
            return

        # Save login
        self.app.current_user = user

        # DIRECT PAGE SWITCH (NO MORE open_admin_page)
        if user.get("role") == "admin":
            self.app.show_page("admin_home")
        else:
            self.app.show_page("adopter_home")
