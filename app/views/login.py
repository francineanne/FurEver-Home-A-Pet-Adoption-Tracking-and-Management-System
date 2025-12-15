from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.config import APP_TITLE, BG_COLOR
from app.controllers.auth_controller import AuthController
from app.widgets.images import safe_ctk_image


class LoginPage(ctk.CTkFrame):
    """
    Login + password reset + signup surface.
    Keeps UI separate from app wiring so App can handle navigation.
    """

    def __init__(self, master, app):
        super().__init__(master, fg_color=BG_COLOR)
        self.app = app
        self.auth = AuthController()
        self.reset_target = {}  # {"email":..., "role":...}

        # Images (loaded safely)
        self.eye_open = safe_ctk_image("eye_open.png", (30, 30))
        self.eye_close = safe_ctk_image("eye_close.png", (30, 30))
        self.paw_right = safe_ctk_image("pawprints_right.png", (150, 150))
        self.paw_left = safe_ctk_image("pawprints_left.png", (150, 150))
        self.puppies = safe_ctk_image("login_background.png", (500, 119))
        self.logo = safe_ctk_image("FurEver_Home_Logo.png", (170, 90))

        # Title row
        title_row = ctk.CTkFrame(self, fg_color=BG_COLOR)
        title_row.place(relx=0.5, rely=0.08, anchor="center")
        ctk.CTkLabel(title_row, image=self.logo, text="").pack(side="left", padx=(0, 16))
        ctk.CTkLabel(
            title_row,
            text=APP_TITLE,
            font=("Georgia", 60, "bold"),
            text_color="white",
        ).pack(side="left")

        # Puppies banner
        ctk.CTkLabel(self, image=self.puppies, text="").place(relx=0.5, rely=0.22, anchor="center")

        # White container
        container = ctk.CTkFrame(
            self,
            width=930,
            height=530,
            corner_radius=80,
            fg_color="#E9F4FF",
            border_width=2,
            border_color="#9EC9FF",
        )
        container.place(relx=0.5, rely=0.58, anchor="center")

        # Login as
        ctk.CTkLabel(container, text="Login as:",
                     font=("Georgia", 28, "bold"),
                     text_color="#00156A").place(relx=0.5, rely=0.10, anchor="center")

        self.dropdown = ctk.CTkOptionMenu(container,
                                          values=["Admin", "Adopter"],
                                          width=620, height=55,
                                          corner_radius=40,
                                          fg_color="#DDE1E6",
                                          button_color="#DDE1E6",
                                          text_color="black",
                                          font=("Georgia", 20))
        self.dropdown.set("Admin")
        self.dropdown.place(relx=0.5, rely=0.18, anchor="center")

        # Email
        ctk.CTkLabel(container, text="Email",
                     font=("Georgia", 28, "bold"),
                     text_color="#00156A").place(relx=0.5, rely=0.28, anchor="center")

        self.email_field = ctk.CTkEntry(container, width=620, height=55,
                                        corner_radius=40, fg_color="#DDE1E6",
                                        font=("Georgia", 20))
        self.email_field.place(relx=0.5, rely=0.36, anchor="center")

        # Password + eye button
        ctk.CTkLabel(container, text="Password",
                     font=("Georgia", 28, "bold"),
                     text_color="#00156A").place(relx=0.5, rely=0.46, anchor="center")

        pw_frame = ctk.CTkFrame(container, width=710, height=55, fg_color="transparent")
        pw_frame.place(relx=0.55, rely=0.54, anchor="center")
        pw_frame.pack_propagate(False)

        self.pw_field = ctk.CTkEntry(
            pw_frame,
            height=55,
            corner_radius=40,
            fg_color="#DDE1E6",
            font=("Georgia", 20),
            show="*",
        )
        self.pw_field.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.eye_button = ctk.CTkButton(
            pw_frame,
            width=55,
            height=55,
            text="",
            fg_color="#DDE1E6",
            hover_color="#c9c9c9",
            corner_radius=40,
            border_width=0,
            image=self.eye_open,
            command=self.toggle_password,
        )
        self.eye_button.pack(side="right")

        # Forgot password
        forgot = ctk.CTkLabel(container, text="Forgot Password",
                              font=("Georgia", 23, "bold"),
                              text_color="#00156A",
                              cursor="hand2")
        forgot.bind("<Button-1>", lambda _e=None: self.open_forgot_password())
        forgot.place(relx=0.5, rely=0.64, anchor="center")

        # Login button
        login_btn = ctk.CTkButton(container, text="Login",
                                  font=("Georgia", 26, "bold"),
                                  width=300, height=55,
                                  corner_radius=50,
                                  fg_color="#002080",
                                  hover_color="#001566",
                                  text_color="white",
                                  command=self.login_action)
        login_btn.place(relx=0.5, rely=0.78, anchor="center")

        # Sign up
        signup_btn = ctk.CTkButton(container, text="Sign Up",
                                   font=("Georgia", 20, "bold"),
                                   width=180, height=46,
                                   corner_radius=40,
                                   fg_color="#0B84FF",
                                   hover_color="#0861BD",
                                   text_color="white",
                                   command=self.open_signup_dialog)
        signup_btn.place(relx=0.5, rely=0.90, anchor="center")

        # Paws (decor)
        ctk.CTkLabel(self, image=self.paw_right, text="").place(relx=0.93, rely=0.14)
        ctk.CTkLabel(self, image=self.paw_left, text="").place(relx=0.97, rely=0.46, anchor="ne")
        ctk.CTkLabel(self, image=self.paw_right, text="").place(relx=0.90, rely=0.82)
        ctk.CTkLabel(self, image=self.paw_left, text="").place(relx=0.015, rely=0.12)
        ctk.CTkLabel(self, image=self.paw_right, text="").place(relx=0.045, rely=0.50)
        ctk.CTkLabel(self, image=self.paw_left, text="").place(relx=0.05, rely=0.81)

    # ----------------------------
    def toggle_password(self):
        if self.pw_field.cget("show") == "*":
            self.pw_field.configure(show="")
            self.eye_button.configure(image=self.eye_close)
        else:
            self.pw_field.configure(show="*")
            self.eye_button.configure(image=self.eye_open)

    # ----------------------------
    def login_action(self):
        role = self.dropdown.get()
        email = self.email_field.get().strip()
        password = self.pw_field.get().strip()

        role_key = "admin" if role.lower().startswith("admin") else "adopter"
        try:
            user = self.auth.login(email, password, role_key)
        except ValueError as e:
            messagebox.showerror("Login Failed", str(e))
            return
        except Exception as e:
            messagebox.showerror("Login Failed", f"An unexpected error occurred.\n{e}")
            return

        self.app.handle_login(role_key, user)

    # ----------------------------
    def open_forgot_password(self):
        win = ctk.CTkToplevel(self)
        win.title("Forgot Password")
        win.geometry("420x320")
        win.grab_set()

        ctk.CTkLabel(win, text="Forgot Password", font=("Georgia", 28, "bold")).pack(pady=(16, 6))

        ctk.CTkLabel(win, text="Role", font=("Georgia", 18)).pack(anchor="w", padx=20, pady=(10, 0))
        role_menu = ctk.CTkOptionMenu(win, values=["Admin", "Adopter"])
        role_menu.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(win, text="Email", font=("Georgia", 18)).pack(anchor="w", padx=20, pady=(10, 0))
        email_entry = ctk.CTkEntry(win, width=360)
        email_entry.pack(fill="x", padx=20, pady=(0, 12))

        status_lbl = ctk.CTkLabel(win, text="", text_color="#555", wraplength=360)
        status_lbl.pack(pady=(6, 0))

        def send_otp():
            email = email_entry.get().strip()
            role_key = "admin" if (role_menu.get() or "").lower().startswith("admin") else "adopter"
            try:
                self.auth.request_otp(email, role_key)
            except Exception as e:
                msg = str(e) if isinstance(e, ValueError) else f"Could not send OTP email.\n{e}"
                messagebox.showerror("Email Error", msg)
                return

            self.reset_target = {"email": email, "role": role_key}
            status_lbl.configure(text=f"OTP sent to {email}. Check your inbox.")
            messagebox.showinfo("OTP Sent", f"An OTP has been sent to {email}.")
            win.destroy()
            self.open_otp_verify()

        ctk.CTkButton(win, text="Send OTP", width=180, command=send_otp).pack(pady=14)

    def open_otp_verify(self):
        if not self.reset_target:
            messagebox.showinfo("Info", "Please request an OTP first.")
            return

        email = self.reset_target.get("email")
        role = self.reset_target.get("role") or "adopter"

        win = ctk.CTkToplevel(self)
        win.title("Verify OTP")
        win.geometry("420x360")
        win.grab_set()

        ctk.CTkLabel(win, text="Verify OTP", font=("Georgia", 28, "bold")).pack(pady=(16, 6))
        ctk.CTkLabel(win, text=f"Email: {email}", text_color="#444").pack(pady=(0, 10))

        ctk.CTkLabel(win, text="Enter OTP", font=("Georgia", 18)).pack(anchor="w", padx=20, pady=(10, 0))
        otp_entry = ctk.CTkEntry(win, width=360)
        otp_entry.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(win, text="New Password", font=("Georgia", 18)).pack(anchor="w", padx=20, pady=(10, 0))
        pw_entry = ctk.CTkEntry(win, width=360, show="*")
        pw_entry.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(win, text="", text_color="#555", wraplength=360).pack(pady=(4, 0))

        def reset_pw():
            code_entered = otp_entry.get().strip()
            new_pw = pw_entry.get().strip()
            try:
                self.auth.reset_password(email, role, code_entered, new_pw)
            except Exception as e:
                msg = str(e) if isinstance(e, ValueError) else f"Could not update password.\n{e}"
                messagebox.showerror("Error", msg)
                return

            messagebox.showinfo("Success", "Password updated. You can now log in with the new password.")
            self.reset_target = {}
            win.destroy()

        ctk.CTkButton(win, text="Reset Password", width=200, command=reset_pw).pack(pady=16)

    # ----------------------------
    def open_signup_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("Sign Up")
        try:
            win.state("zoomed")
        except Exception:
            win.geometry("1366x768")
        try:
            # ensure it covers the screen if zoom isn't supported
            win.update_idletasks()
            w, h = win.winfo_screenwidth(), win.winfo_screenheight()
            win.geometry(f"{w}x{h}+0+0")
        except Exception:
            pass
        win.configure(fg_color=BG_COLOR)
        win.grab_set()

        ctk.CTkLabel(win, text=APP_TITLE, font=("Georgia", 60, "bold"), text_color="white").place(relx=0.5, rely=0.08, anchor="center")
        ctk.CTkLabel(win, image=self.puppies, text="").place(relx=0.5, rely=0.22, anchor="center")

        container = ctk.CTkFrame(
            win,
            width=930,
            height=580,
            corner_radius=0,
            fg_color="#E9F4FF",
            border_width=2,
            border_color="#9EC9FF",
        )
        container.place(relx=0.5, rely=0.62, anchor="center")
        container.pack_propagate(False)

        shell = ctk.CTkFrame(container, fg_color="white", corner_radius=0)
        shell.pack(fill="both", expand=True, padx=18, pady=16)
        shell.pack_propagate(False)

        header = ctk.CTkFrame(shell, fg_color="white")
        header.pack(fill="x", pady=(18, 0))
        ctk.CTkLabel(header, text="Create Account", font=("Georgia", 28, "bold"), text_color="#00156A").pack(anchor="center")
        ctk.CTkLabel(header, text="Choose role and enter your information.", font=("Georgia", 16), text_color="#00156A").pack(anchor="center", pady=(6, 10))

        form = ctk.CTkScrollableFrame(shell, fg_color="white", corner_radius=0)
        form.pack(fill="both", expand=True, padx=26, pady=(0, 12))
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=0)

        fields = {}
        row_idx = 0

        def add_field(label, key, show=None):
            nonlocal row_idx
            ctk.CTkLabel(form, text=label, font=("Georgia", 16), text_color="#00156A").grid(row=row_idx, column=0, sticky="w", pady=(0, 10), padx=(4, 12))
            entry = ctk.CTkEntry(
                form,
                width=350,
                height=35,
                corner_radius=30,
                fg_color="#DDE1E6",
                font=("Georgia", 14),
                show=show,
            )
            entry.grid(row=row_idx, column=1, sticky="w", pady=(0, 10))
            fields[key] = entry
            row_idx += 1

        ctk.CTkLabel(form, text="Role", font=("Georgia", 16), text_color="#00156A").grid(row=row_idx, column=0, sticky="w", pady=(0, 12), padx=(4, 12))
        role_menu = ctk.CTkOptionMenu(
            form,
            values=["Adopter", "Admin"],
            width=350,
            height=35,
            corner_radius=30,
            fg_color="#DDE1E6",
            button_color="#DDE1E6",
            text_color="black",
            font=("Georgia", 14),
        )
        role_menu.grid(row=row_idx, column=1, sticky="w", pady=(0, 12))
        row_idx += 1

        add_field("Full Name", "name")
        add_field("Email", "email")
        add_field("Phone", "phone")
        add_field("Birthdate (YYYY-MM-DD)", "birthdate")
        add_field("Password", "password", show="*")
        add_field("Confirm Password", "confirm", show="*")

        # Photo upload
        ctk.CTkLabel(form, text="Photo (optional)", font=("Georgia", 16), text_color="#00156A").grid(
            row=row_idx, column=0, sticky="w", pady=(0, 10), padx=(4, 12)
        )
        photo_frame = ctk.CTkFrame(form, fg_color="white")
        photo_frame.grid(row=row_idx, column=1, sticky="w", pady=(0, 10))
        photo_entry = ctk.CTkEntry(
            photo_frame,
            width=240,
            height=35,
            corner_radius=30,
            fg_color="#DDE1E6",
            font=("Georgia", 14),
        )
        photo_entry.pack(side="left", pady=(0, 2))

        def browse_photo():
            path = filedialog.askopenfilename(
                title="Select photo",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("All Files", "*.*")]
            )
            if path:
                photo_entry.delete(0, "end")
                photo_entry.insert(0, path)

        ctk.CTkButton(
            photo_frame,
            text="Browse",
            width=90,
            height=35,
            corner_radius=24,
            fg_color="#0B84FF",
            hover_color="#0861BD",
            command=browse_photo,
        ).pack(side="left", padx=(8, 0))
        fields["photo"] = photo_entry
        row_idx += 1

        def submit_signup():
            role = role_menu.get().strip() or "Adopter"
            name = fields["name"].get().strip()
            email = fields["email"].get().strip()
            phone = fields["phone"].get().strip()
            birthdate = fields["birthdate"].get().strip()
            password = fields["password"].get().strip()
            confirm = fields["confirm"].get().strip()
            photo_path = fields.get("photo").get().strip() if fields.get("photo") else ""
            instagram_url = ""

            try:
                role_key = self.auth.signup(
                    role,
                    name,
                    email,
                    password,
                    confirm,
                    phone,
                    birthdate,
                    photo_path,
                    "",
                    instagram_url,
                )
                if role_key == "admin":
                    messagebox.showinfo("Submitted", "Your admin request was submitted. An existing admin must approve it.")
                else:
                    messagebox.showinfo("Account Created", "Adopter account created. Please log in.")
                win.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                return
            except Exception as e:
                messagebox.showerror("Error", str(e))

        actions = ctk.CTkFrame(shell, fg_color="white")
        actions.pack(fill="x", pady=(4, 16))
        ctk.CTkButton(
            actions,
            text="Cancel",
            font=("Georgia", 20, "bold"),
            width=160,
            height=38,
            corner_radius=32,
            fg_color="#D64545",
            hover_color="#B53030",
            text_color="white",
            command=win.destroy,
        ).pack(side="left", padx=(16, 8), pady=4)
        ctk.CTkButton(
            actions,
            text="Sign Up",
            font=("Georgia", 24, "bold"),
            width=200,
            height=40,
            corner_radius=40,
            fg_color="#0B84FF",
            hover_color="#0861BD",
            text_color="white",
            command=submit_signup,
        ).pack(side="right", padx=(8, 16), pady=4)
