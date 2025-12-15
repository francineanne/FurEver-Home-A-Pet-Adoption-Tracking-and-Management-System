import os
import webbrowser
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageOps

from app.config import ASSETS_DIR, BASE_DIR, IMAGES_DIR
from app.controllers import AdopterController
from app.services.pet_components import load_pet_image
ctk.set_appearance_mode("light")

LOGO_FILE = "FurEver_Home_Logo.png"
_HEADER_LOGO = None
PROJECT_ROOT = Path(BASE_DIR)
ASSETS_ROOT = Path(ASSETS_DIR)
IMAGES_ROOT = Path(IMAGES_DIR)


def _get_header_logo(size=(130, 70)):
    """
    Load and cache the shared logo for all adopter screens.
    """
    global _HEADER_LOGO
    if _HEADER_LOGO is not None:
        return _HEADER_LOGO if _HEADER_LOGO else None

    try:
        path = ASSETS_ROOT / LOGO_FILE
        if not path.exists():
            _HEADER_LOGO = False
            return None
        img = Image.open(path).convert("RGBA")
        _HEADER_LOGO = ctk.CTkImage(img, size=size)
        return _HEADER_LOGO
    except Exception:
        _HEADER_LOGO = False
        return None


def make_header(parent, title="FurEver Home", subtitle=None):
    header = ctk.CTkFrame(parent, fg_color="#042b66", corner_radius=0)
    header.pack(fill="x")

    row = ctk.CTkFrame(header, fg_color="#042b66")
    row.pack(side="left", padx=25, pady=10)

    logo = _get_header_logo()
    if logo:
        logo_lbl = ctk.CTkLabel(row, image=logo, text="")
        logo_lbl.image = logo
        logo_lbl.pack(side="left", padx=(0, 14))

    text_block = ctk.CTkFrame(row, fg_color="#042b66")
    text_block.pack(side="left")
    ctk.CTkLabel(text_block, text=title, font=("Georgia", 34, "bold"), text_color="white").pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(text_block, text=subtitle, font=("Georgia", 14), text_color="white").pack(anchor="w")
    return header


class AdopterHomePage(ctk.CTkFrame):
    def __init__(self, master, app, switch_frame=None):
        super().__init__(master)
        self.app = app
        self.switch_frame = switch_frame
        self.controller = AdopterController()
        self.user = app.current_user or {}

        self.configure(fg_color="#f2f5fa")
        self.pack(fill="both", expand=True)

        make_header(self, "Furever Home", "Find your future pet companion.")

        container = ctk.CTkFrame(self, fg_color="#f2f5fa")
        container.pack(fill="both", expand=True)

        sidebar = ctk.CTkFrame(container, width=230, fg_color="#d9e6f2", corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="Menu", font=("Georgia", 24, "bold"), text_color="#072658").pack(pady=(20, 10))

        def sb_btn(text, command):
            return ctk.CTkButton(
                sidebar,
                text=text,
                width=180,
                height=44,
                fg_color="#1b63d1",  # Blue color for buttons
                hover_color="#154ea8",
                font=("Georgia", 14),
                command=command,
            )

        sb_btn("Available Pets", self.show_pet_list).pack(pady=5)
        sb_btn("My Requests", self.show_requests).pack(pady=5)
        sb_btn("Notifications", self.show_notifications).pack(pady=5)
        sb_btn("Adoption History", self.show_history).pack(pady=5)
        sb_btn("Profile", self.show_profile).pack(pady=5)
        sb_btn("Help Center", self.show_help_center).pack(pady=5)
        sb_btn("About Us", self.show_about).pack(pady=5)

        # Move the Logout button to the bottom of the sidebar by using pack(side="bottom")
        ctk.CTkButton(
            sidebar,
            text="Logout",
            fg_color="#d64545",  # Logout button color
            hover_color="#b23333",
            width=200,
            height=44,
            font=("Georgia", 14),
            command=lambda: app.show_page("login"),  # Ensure this takes the user to the login page
        ).pack(side="bottom", pady=30)

        self.content = ctk.CTkFrame(container, fg_color="#f2f5fa")
        self.content.pack(side="left", fill="both", expand=True)

        self.show_pet_list()

    def clear(self):
        for w in list(self.content.winfo_children()):
            w.destroy()

    def _get_user_id(self):
        """
        Normalize adopter id lookups (some logins store `users_id`, others `id`/`user_id`).
        """
        user = self.app.current_user or self.user or {}
        return (
            user.get("users_id")
            or user.get("user_id")
            or user.get("id")
            or user.get("adopter_id")
        )

    # --------------------------------------------------
    # Available Pets (matches admin/manage style)
    # --------------------------------------------------
    def show_pet_list(self):
        self.clear()
        bg = ctk.CTkFrame(self.content, fg_color="#06215A")
        bg.pack(fill="both", expand=True)

        ctk.CTkLabel(bg, text="Available Pets", font=("Georgia", 40, "bold"), text_color="white").pack(
            anchor="center", pady=(32, 6)
        )
        ctk.CTkLabel(bg, text="Browse and apply to adopt.", font=("Georgia", 18), text_color="white").pack(
            anchor="center", pady=(0, 24)
        )

        # Filter bar
        filter_bar = ctk.CTkFrame(bg, fg_color="#052a6c", corner_radius=14)
        filter_bar.pack(fill="x", padx=50, pady=(0, 16))

        ctk.CTkLabel(filter_bar, text="Category", font=("Georgia", 16), text_color="white").pack(
            side="left", padx=(14, 10), pady=12
        )

        categories = ["All", "dog", "cat"]
        self.adopter_category_combo = ctk.CTkComboBox(
            filter_bar,
            values=categories,
            width=180,
            fg_color="#0e3f9a",
            button_color="#0e3f9a",
            text_color="white",
            state="readonly",
        )
        current_cat = getattr(self, "adopter_category", "All")
        self.adopter_category_combo.set(current_cat)
        self.adopter_category_combo.pack(side="left", pady=10)

        def apply_filter():
            self.adopter_category = self.adopter_category_combo.get() or "All"
            self._render_pet_cards(bg)

        def reset_filter():
            self.adopter_category = "All"
            self.adopter_category_combo.set("All")
            self._render_pet_cards(bg)

        ctk.CTkButton(
            filter_bar, text="Filter", width=120, fg_color="#265AAD", hover_color="#73A7FC", command=apply_filter
        ).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(
            filter_bar, text="Reset", width=120, fg_color="#BF2121", hover_color="#374151", command=reset_filter
        ).pack(side="left", padx=6, pady=10)

        scroll = ctk.CTkScrollableFrame(bg, fg_color="#06215A", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=50, pady=(8, 32))
        self.pet_scroll = scroll
        self._render_pet_cards(bg)

    def _render_pet_cards(self, bg):
        # clear existing grid in scroll
        for w in list(self.pet_scroll.winfo_children()):
            w.destroy()

        # fetch pets with category filter
        cat = getattr(self, "adopter_category", "All")
        try:
            pets = self.controller.list_pets(cat)
        except Exception:
            pets = []

        if not pets:
            ctk.CTkLabel(self.pet_scroll, text="No pets available right now.", font=("Georgia", 18), text_color="white").pack(
                pady=24
            )
            return

        grid = ctk.CTkFrame(self.pet_scroll, fg_color="#06215A")
        grid.pack()
        cols = 3
        row = 0
        col = 0

        image_size = (260, 190)

        for pet in pets:
            card = ctk.CTkFrame(grid, fg_color="white", corner_radius=28, width=340, height=520)
            card.grid(row=row, column=col, padx=20, pady=20)
            card.pack_propagate(False)

            try:
                img = load_pet_image(pet.get("image") or pet.get("photo") or pet.get("photo_path"), size=image_size)
                img_lbl = ctk.CTkLabel(card, image=img, text="", width=image_size[0], height=image_size[1])
                img_lbl.image = img
                img_lbl.pack(pady=(18, 10))
            except Exception:
                placeholder = ctk.CTkLabel(card, text="No Image", width=image_size[0], height=image_size[1], fg_color="#D9D9D9")
                placeholder.pack(pady=(18, 10))

            name = pet.get("name") or pet.get("pet_name") or "Unknown"
            breed = pet.get("breed", "Unknown")
            age = pet.get("age", "N/A")
            sex = pet.get("sex", "N/A")
            desc = pet.get("description") or ""

            ctk.CTkLabel(card, text=name, font=("Georgia", 17, "bold"), text_color="#000").pack(
                anchor="w", padx=18
            )
            ctk.CTkLabel(
                card, text=f"{breed} • {age} yrs • {sex}", font=("Georgia", 12), text_color="#444"
            ).pack(anchor="w", padx=18, pady=(0, 4))
            status_val = pet.get("status") or "available"
            vaccinated_val = pet.get("vaccinated")
            vaccinated_txt = "Yes" if str(vaccinated_val).strip().lower() in ("1", "true", "yes") else "No/Unknown"
            ctk.CTkLabel(
                card, text=f"Status: {status_val.title() if isinstance(status_val, str) else status_val} • Vaccinated: {vaccinated_txt}",
                font=("Georgia", 11), text_color="#555"
            ).pack(anchor="w", padx=18, pady=(0, 4))
            ctk.CTkLabel(
                card, text=desc, wraplength=300, justify="left", font=("Georgia", 12), text_color="#555"
            ).pack(anchor="w", padx=18, pady=(6, 14))

            btn_frame = ctk.CTkFrame(card, fg_color="white")
            btn_frame.pack(side="bottom", pady=(0, 18))

            ctk.CTkButton(
                btn_frame,
                text="View Details",
                width=130,
                height=36,
                fg_color="#1E63D1",
                hover_color="#174DA6",
                corner_radius=12,
                font=("Georgia", 13, "bold"),
                command=lambda p=pet: self.open_pet_details(p),
            ).pack(side="left", padx=8)

            ctk.CTkButton(
                btn_frame,
                text="Adopt",
                width=130,
                height=36,
                fg_color="#4CAF50",
                hover_color="#43A047",
                corner_radius=12,
                font=("Georgia", 13, "bold"),
                command=lambda p=pet: self.open_adoption_form(p),
            ).pack(side="left", padx=8)

            col += 1
            if col >= cols:
                col = 0
                row += 1

    # --------------------------------------------------
    def open_pet_details(self, pet):
        win = ctk.CTkToplevel(self)
        win.title(pet.get("name", "Pet Details"))
        win.geometry("520x560")
        win.configure(fg_color="#f8fafc")

        try:
            img = load_pet_image(pet.get("image") or pet.get("photo") or pet.get("photo_path"), size=(200, 200))
            lbl = ctk.CTkLabel(win, image=img, text="")
            lbl.image = img
            lbl.pack(pady=12)
        except Exception:
            pass

        name = pet.get("name") or "Unknown"
        breed = pet.get("breed") or "Unknown"
        age = pet.get("age") or "N/A"
        sex = pet.get("sex") or "N/A"
        vaccinated_val = pet.get("vaccinated")
        status_val = pet.get("status") or "available"
        vaccinated_txt = "Yes" if str(vaccinated_val).strip().lower() in ("1", "true", "yes") else "No/Unknown"
        desc = pet.get("description") or "No description available."

        info = (
            f"Name: {name}\n"
            f"Breed: {breed}\n"
            f"Age: {age}\n"
            f"Sex: {sex}\n"
            f"Vaccinated: {vaccinated_txt}\n"
            f"Status: {status_val}\n\n"
            f"Description:\n{desc}"
        )
        ctk.CTkLabel(win, text=info, font=("Arial", 12), wraplength=480, justify="left").pack(padx=12, pady=12)
        ctk.CTkButton(win, text="Close", width=120, command=win.destroy).pack(pady=10)

    # --------------------------------------------------
    def open_adoption_form(self, pet):
        form = ctk.CTkToplevel(self)
        form.title("Adoption Application")
        form.geometry("700x820")
        form.configure(fg_color="#FAFAFA")

        ctk.CTkLabel(form, text="Adoption Application", font=("Georgia", 28, "bold")).pack(pady=(14, 4))
        pet_name = pet.get("name") or pet.get("pet_name") or ""
        breed = pet.get("breed") or ""
        ctk.CTkLabel(form, text=f"Pet: {pet_name} ({breed})", font=("Georgia", 14), text_color="#444").pack(pady=(0, 10))

        # Pet photo preview
        preview = ctk.CTkFrame(form, fg_color="#FAFAFA")
        preview.pack(pady=(0, 8))
        pet_photo_path = (
            pet.get("image_resolved")
            or pet.get("photo")
            or pet.get("image")
            or pet.get("pet_image")
            or pet.get("pet_photo")
        )
        if pet_photo_path:
            try:
                pet_img = load_pet_image(pet_photo_path, size=(220, 180))
                lbl = ctk.CTkLabel(preview, image=pet_img, text="")
                lbl.image = pet_img
                lbl.pack()
            except Exception:
                ctk.CTkLabel(preview, text="No Image", font=("Georgia", 12), text_color="#666",
                             width=220, height=180, fg_color="#e5e7eb", corner_radius=8).pack()
        else:
            ctk.CTkLabel(preview, text="No Image", font=("Georgia", 12), text_color="#666",
                         width=220, height=180, fg_color="#e5e7eb", corner_radius=8).pack()

        body = ctk.CTkScrollableFrame(form, width=640, fg_color="#FAFAFA")
        body.pack(fill="both", expand=True, padx=20)

        entries = {}

        def field(label, key, prefill=""):
            ctk.CTkLabel(body, text=label, font=("Georgia", 14)).pack(anchor="w", padx=6, pady=(10, 0))
            ent = ctk.CTkEntry(body, width=600)
            ent.insert(0, prefill)
            ent.pack(padx=6, pady=(0, 6))
            entries[key] = ent

        field("Full Name", "fullname", self.user.get("name", ""))
        field("Email Address", "email", self.user.get("email", ""))
        field("Phone Number", "phone", self.user.get("phone", ""))
        field("Home Address", "address", "")
        ctk.CTkLabel(body, text="Do you have any prior experience with pet care or adoption?", font=("Georgia", 14)).pack(anchor="w", padx=6, pady=(10, 0))
        experience_var = ctk.BooleanVar(value=False)
        exp_row = ctk.CTkFrame(body, fg_color="#FAFAFA")
        exp_row.pack(fill="x", padx=6, pady=(0, 6))
        ctk.CTkCheckBox(exp_row, text="Yes", variable=experience_var).pack(side="left")
        ctk.CTkCheckBox(exp_row, text="No", variable=experience_var, onvalue=False, offvalue=True).pack(side="left", padx=(8,0))
        ctk.CTkLabel(exp_row, text="If yes, how many?", font=("Georgia", 12)).pack(side="left", padx=(10, 4))
        exp_count = ctk.CTkEntry(exp_row, width=120)
        exp_count.pack(side="left")

        ctk.CTkLabel(body, text="Why do you want to adopt this pet?", font=("Georgia", 14)).pack(anchor="w", padx=6, pady=(10, 0))
        reason_box = ctk.CTkTextbox(body, width=600, height=140, corner_radius=6, fg_color="#FFFFFF", text_color="#111")
        reason_box.pack(padx=6, pady=(0, 10))

        ctk.CTkLabel(body, text="Agreement", font=("Georgia", 14, "bold")).pack(anchor="w", padx=6, pady=(12, 2))
        ctk.CTkLabel(
            body,
            text="Please review and accept the Terms & Conditions and Privacy Policy before submitting.",
            font=("Georgia", 11),
            text_color="#374151",
        ).pack(anchor="w", padx=6, pady=(0, 6))

        agree_frame = ctk.CTkFrame(body, fg_color="#eef2ff", corner_radius=8)
        agree_frame.pack(anchor="w", fill="x", padx=4, pady=(0, 10))

        agree_var = ctk.BooleanVar(value=False)

        # Checkbox for agreement
        ctk.CTkCheckBox(agree_frame, text="I have read and accept", variable=agree_var).pack(side="left", padx=(8, 6), pady=8)

        # Text + clickable Terms/Privacy links
        text_frame = ctk.CTkFrame(agree_frame, fg_color="transparent")
        text_frame.pack(side="left", pady=8)

        terms_label = ctk.CTkLabel(
            text_frame,
            text="Terms & Conditions",
            font=("Georgia", 12, "underline"),
            text_color="#1E63D1",
            cursor="hand2",
        )
        terms_label.pack(side="left")
        ctk.CTkLabel(text_frame, text=" and ", font=("Georgia", 12), text_color="#000").pack(side="left")
        privacy_label = ctk.CTkLabel(
            text_frame,
            text="Privacy Policy",
            font=("Georgia", 12, "underline"),
            text_color="#1E63D1",
            cursor="hand2",
        )
        privacy_label.pack(side="left")

        def show_terms_popup(event=None):
            terms_win = ctk.CTkToplevel(form)
            terms_win.title("Terms & Conditions")
            terms_win.geometry("600x500")
            terms_win.configure(fg_color="#FAFAFA")

            txt = ctk.CTkTextbox(terms_win, width=560, height=440, wrap="word", font=("Georgia", 12))
            txt.pack(padx=20, pady=20, fill="both", expand=True)
            txt.insert("0.0", self.help_terms())
            txt.configure(state="disabled")

        terms_label.bind("<Button-1>", show_terms_popup)

        def show_privacy_popup(event=None):
            privacy_win = ctk.CTkToplevel(form)
            privacy_win.title("Privacy Policy")
            privacy_win.geometry("600x500")
            privacy_win.configure(fg_color="#FAFAFA")

            txt = ctk.CTkTextbox(privacy_win, width=560, height=440, wrap="word", font=("Georgia", 12))
            txt.pack(padx=20, pady=20, fill="both", expand=True)
            txt.insert("0.0", self.help_privacy())
            txt.configure(state="disabled")

        privacy_label.bind("<Button-1>", show_privacy_popup)

        bottom = ctk.CTkFrame(form, fg_color="#FAFAFA")
        bottom.pack(fill="x", pady=14)

        def submit():
            if not agree_var.get():
                messagebox.showerror("Error", "You must agree to the Terms & Conditions and Privacy Policy before submitting.")
                return

            user_id = self._get_user_id()
            if not user_id:
                messagebox.showerror("Error", "Cannot submit: adopter ID not found.")
                return

            pet_pk = pet.get("id") or pet.get("pet_id")
            if not pet_pk:
                messagebox.showerror("Error", "Cannot submit: pet ID not found.")
                return

            # Avoid duplicate pending requests for the same pet
            try:
                if self.controller.has_pending_request(user_id, pet_pk):
                    messagebox.showinfo("Already Requested", "You already have a pending request for this pet.")
                    return
            except Exception:
                pass

            note = "\n".join(
                [
                    f"Full Name: {entries['fullname'].get().strip()}",
                    f"Email: {entries['email'].get().strip()}",
                    f"Phone: {entries['phone'].get().strip()}",
                    f"Address: {entries['address'].get().strip()}",
                    f"Experience caring for pets: {'Yes' if experience_var.get() else 'No'}",
                    f"How many (if yes): {exp_count.get().strip() if experience_var.get() else 'N/A'}",
                    f"Reason: {reason_box.get('1.0', 'end').strip()}",
                ]
            )

            try:
                self.controller.submit_request(user_id, pet_pk, note, pet_name)
                messagebox.showinfo("Success", "Your application has been submitted.")
                form.destroy()
                self.show_requests()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to submit application.\n{e}")

        ctk.CTkButton(bottom, text="Submit", width=180, fg_color="#4CAF50", hover_color="#43A047", command=submit).pack(
            side="right", padx=(0, 10)
        )
        ctk.CTkButton(
            bottom, text="Cancel", width=140, fg_color="#D9534F", hover_color="#C9302C", command=form.destroy
        ).pack(side="right", padx=(0, 10))

    # --------------------------------------------------
    def show_requests(self):
        self.clear()
        make_header(self.content, "My Adoption Requests")

        hero = ctk.CTkFrame(self.content, fg_color="#00156A")
        hero.pack(fill="both", expand=True)

        ctk.CTkLabel(hero, text="My Adoption Requests", font=("Georgia", 44, "bold"), text_color="white").pack(
            pady=(22, 6)
        )
        ctk.CTkLabel(hero, text="Track your submitted adoption requests and their status.", font=("Georgia", 16),
                     text_color="#D4FAFF").pack(pady=(0, 18))

        shell = ctk.CTkFrame(hero, width=1040, height=640, corner_radius=40, fg_color="#D4FAFF", border_width=2, border_color="#9EC9FF")
        shell.pack(fill="both", expand=True, padx=22, pady=(0, 26))
        shell.pack_propagate(False)

        # Status filter
        filter_bar = ctk.CTkFrame(shell, fg_color="#cfe4ff", corner_radius=14)
        filter_bar.pack(fill="x", padx=20, pady=(16, 6))

        ctk.CTkLabel(filter_bar, text="Status", font=("Georgia", 14, "bold"), text_color="#0a2c68").pack(side="left", padx=12, pady=10)
        status_values = ["All", "Pending", "Approved", "Cancelled", "Rejected"]
        self.request_status_filter = getattr(self, "request_status_filter", "All")
        status_combo = ctk.CTkComboBox(
            filter_bar,
            values=status_values,
            width=180,
            state="readonly",
            fg_color="#0e3f9a",
            button_color="#0e3f9a",
            text_color="white",
        )
        status_combo.set(self.request_status_filter)
        status_combo.pack(side="left", pady=10)

        def apply_filter():
            self.request_status_filter = status_combo.get() or "All"
            self.show_requests()

        def reset_filter():
            self.request_status_filter = "All"
            status_combo.set("All")
            self.show_requests()

        ctk.CTkButton(filter_bar, text="Apply", width=100, fg_color="#265AAD", hover_color="#73A7FC", command=apply_filter).pack(
            side="left", padx=8, pady=10
        )
        ctk.CTkButton(filter_bar, text="Reset", width=100, fg_color="#BF2121", hover_color="#374151", command=reset_filter).pack(
            side="left", padx=4, pady=10
        )

        scroll = ctk.CTkScrollableFrame(shell, fg_color="#D4FAFF")
        scroll.pack(fill="both", expand=True, padx=20, pady=(8, 18))

        user_id = self._get_user_id()
        if not user_id:
            messagebox.showerror("Error", "Cannot show requests: adopter ID not found.")
            return

        try:
            requests = self.controller.list_requests(user_id, getattr(self, "request_status_filter", "All"))
        except Exception as e:
            messagebox.showerror("Error", f"Unable to fetch requests.\n{e}")
            return
        status_filter = getattr(self, "request_status_filter", "All")

        if not requests:
            empty_msg = "No adoption requests submitted yet." if status_filter.lower() == "all" else "No requests match the selected status."
            ctk.CTkLabel(scroll, text=empty_msg, font=("Georgia", 14), text_color="#666").pack(pady=16)
            return

        def resolve_photo(photo_path, size=(80, 80)):
            if not photo_path:
                return None
            normalized = str(photo_path).replace("\\", "/")
            if normalized.startswith("images/"):
                normalized = normalized.split("/", 1)[1]
            candidates = []
            if os.path.isabs(photo_path):
                candidates.append(photo_path)
            candidates.append(str(IMAGES_ROOT / normalized))
            candidates.append(str(ASSETS_ROOT / normalized))
            for path in candidates:
                if os.path.exists(path):
                    try:
                        return load_pet_image(path, size=size)
                    except Exception:
                        continue
            return None

        def open_request_detail(req):
            # ---------------------------
            # LOAD DATA
            # ---------------------------
            try:
                full = self.controller.get_request(req.get("id"))
            except Exception:
                full = req

            status_raw = (full or {}).get("status") or req.get("status", "pending")

            # ---------------------------
            # MAIN WINDOW
            # ---------------------------
            detail = ctk.CTkToplevel(self)
            detail.title("Adoption Request Details")
            detail.geometry("900x820")
            detail.configure(fg_color="#0C2D48")   # dark blue tone
            detail.resizable(False, False)

            # =============================
            #   TWO-TONE BACKGROUND
            # =============================
            top_frame = ctk.CTkFrame(detail, fg_color="#145DA0")  # lighter blue
            top_frame.pack(fill="x", pady=0)

            body_frame = ctk.CTkFrame(detail, fg_color="#FFFFFF")
            body_frame.pack(fill="both", expand=True, pady=(0, 5), padx=5)

            # =============================
            #   HEADER — PET CALLING ADOPTER
            # =============================
            title_text = (
                f"{full.get('pet_name')} is calling {full.get('adopter_name')}!"
                if full else "Adoption Request"
            )

            ctk.CTkLabel(
                top_frame,
                text=title_text,
                font=("Georgia", 26, "bold"),
                text_color="white"
            ).pack(pady=20)

            # ===========================================================
            #   PET ID TAG HEADER
            # ===========================================================
            id_tag = ctk.CTkFrame(body_frame, fg_color="#145DA0", corner_radius=50)
            id_tag.pack(fill="x", padx=40, pady=(20, 0))

            ctk.CTkLabel(
                id_tag,
                text="Adoption Application Details",
                font=("Georgia", 22, "bold"),
                text_color="white"
            ).pack(pady=10)

            # ===========================================================
            #   CALLING CARD AREA
            # ===========================================================
            calling_card = ctk.CTkFrame(body_frame, fg_color="white", corner_radius=20)
            calling_card.pack(fill="x", padx=20, pady=10)

            calling_card.grid_columnconfigure(0, weight=1)
            calling_card.grid_columnconfigure(1, weight=0)
            calling_card.grid_columnconfigure(2, weight=1)

            # --------------------------
            # PET PHOTO (LEFT)
            # --------------------------
            pet_photo = full.get("pet_image_resolved") if full else None
            try:
                pet_img = load_pet_image(pet_photo, size=(260, 240))
            except Exception:
                pet_img = None

            pet_photo_frame = ctk.CTkFrame(calling_card, fg_color="white", corner_radius=20)
            pet_photo_frame.grid(row=0, column=0, padx=20, pady=20)

            if pet_img:
                pet_pic = ctk.CTkLabel(
                    pet_photo_frame,
                    image=pet_img,
                    text="",
                    corner_radius=20
                )
                pet_pic.image = pet_img
                pet_pic.pack()
            else:
                ctk.CTkLabel(
                    pet_photo_frame,
                    text="No Pet Photo",
                    width=240,
                    height=200,
                    fg_color="#e5e7eb",
                    text_color="#555",
                    corner_radius=20
                ).pack()

            # ==========================
            # BLUE DIVIDER LINE
            # ==========================
            line = ctk.CTkFrame(calling_card, fg_color="#145DA0", width=4, height=200)
            line.grid(row=0, column=1, padx=10, pady=10)

            # --------------------------
            # ADOPTER PHOTO (RIGHT)
            # --------------------------
            adopter_photo = resolve_photo((full or {}).get("adopter_photo"), size=(240, 240))

            adopter_photo_frame = ctk.CTkFrame(calling_card, fg_color="white", corner_radius=20)
            adopter_photo_frame.grid(row=0, column=2, padx=20, pady=20)

            if adopter_photo:
                adopter_pic = ctk.CTkLabel(
                    adopter_photo_frame,
                    image=adopter_photo,
                    text="",
                    corner_radius=20
                )
                adopter_pic.image = adopter_photo
                adopter_pic.pack()
            else:
                ctk.CTkLabel(
                    adopter_photo_frame,
                    text="No Photo",
                    width=240,
                    height=200,
                    fg_color="#e5e7eb",
                    text_color="#555",
                    corner_radius=20
                ).pack()

            # ===========================================================
            #   DECLINED STAMP (approved overlay removed)
            # ===========================================================
            stamp_img = None
            if status_raw.lower() in ("declined", "rejected"):
                stamp_file = "rejected.png"

                for sp in [ASSETS_ROOT / stamp_file]:
                    if os.path.exists(sp):
                        try:
                            stamp = Image.open(sp).resize((220, 160))
                            stamp_img = ctk.CTkImage(stamp)
                        except Exception:
                            stamp_img = None
                        break

            if stamp_img:
                stamp_lbl = ctk.CTkLabel(calling_card, image=stamp_img, text="")
                stamp_lbl.image = stamp_img
                stamp_lbl.place(x=300, y=10)

            # ===========================================================
            #   FULL APPLICATION INFO (CENTERED CARD WITH SHADOW)
            # ===========================================================
            shadow_frame = ctk.CTkFrame(body_frame, fg_color="#E5E7EB", corner_radius=25)
            shadow_frame.pack(fill="both", expand=False, padx=18, pady=(10, 20))

            info_frame = ctk.CTkFrame(shadow_frame, fg_color="white", corner_radius=20)
            info_frame.pack(fill="both", expand=True, padx=4, pady=4)

            info_text = (
                f"{full.get('pet_name')} ({full.get('breed')})\n\n"
                f"{full.get('reason') or '—'}"
            )

            info_label = ctk.CTkLabel(
                info_frame,
                text=info_text,
                font=("Georgia", 16),
                text_color="#0F172A",
                justify="center",
                wraplength=700
            )
            info_label.pack(expand=True, pady=30)

            # ===========================================================
            #   ACTION BUTTONS (view only for adopters)
            # ===========================================================
            buttons = ctk.CTkFrame(detail, fg_color="#0C2D48")
            buttons.pack(fill="x", pady=(5, 15))

            status_lc = status_raw.lower()
            if status_lc in ("approved", "declined", "rejected"):
                ctk.CTkButton(
                    buttons,
                    text="Download Form",
                    width=170,
                    fg_color="#1E63D1",
                    hover_color="#174DA6",
                    command=lambda: self._download_adoption_form(full or req, status_lc),
                ).pack(side="left", padx=20, pady=8)

            ctk.CTkButton(
                buttons,
                text="Close",
                width=140,
                fg_color="#4B5563",
                hover_color="#374151",
                command=detail.destroy,
            ).pack(side="right", padx=20, pady=8)

        for r in requests:
            card = ctk.CTkFrame(scroll, fg_color="white", corner_radius=16, border_width=1, border_color="#b7d4ff")
            card.pack(fill="x", padx=8, pady=8)

            pet_name = r.get("pet_name", "Unknown Pet")
            status_raw = str(r.get("status", "pending")).strip().lower()
            status = status_raw.title()
            created = r.get("created_at") or r.get("requested_at") or ""
            req_id = r.get("id")
            pet_photo = r.get("pet_image_resolved") or r.get("pet_photo") or r.get("pet_image") or ""

            row = ctk.CTkFrame(card, fg_color="#f8fafc")
            row.pack(fill="x", padx=6, pady=6)

            thumb_frame = ctk.CTkFrame(row, fg_color="#f8fafc")
            thumb_frame.pack(side="left", padx=10, pady=6)
            try:
                thumb_img = load_pet_image(pet_photo, size=(120, 90))
                lbl = ctk.CTkLabel(thumb_frame, image=thumb_img, text="")
                lbl.image = thumb_img
                lbl.pack()
            except Exception:
                ctk.CTkLabel(thumb_frame, text="No Image", fg_color="#e5e7eb", width=120, height=90).pack()

            info = ctk.CTkFrame(row, fg_color="#f8fafc")
            info.pack(side="left", fill="both", expand=True, padx=8, pady=4)
            ctk.CTkLabel(info, text=pet_name, font=("Georgia", 16, "bold"), text_color="#111").pack(
                anchor="w", padx=6, pady=(2, 0)
            )
            ctk.CTkLabel(info, text=f"Status: {status}", font=("Georgia", 13), text_color="#444").pack(anchor="w", padx=6)
            ctk.CTkLabel(info, text=f"Submitted on: {created}", font=("Georgia", 12), text_color="#666").pack(
                anchor="w", padx=6, pady=(0, 4)
            )

            btns = ctk.CTkFrame(row, fg_color="#f8fafc")
            btns.pack(side="right", padx=8, pady=6)

            def delete_request(req=req_id):
                if not messagebox.askyesno("Delete Request", "Delete this request? This cannot be undone."):
                    return
                try:
                    ok = self.controller.delete_request(req, adopter_id=user_id)
                except Exception as e:
                    messagebox.showerror("Error", f"Unable to delete request.\n{e}")
                    return
                if ok:
                    messagebox.showinfo("Deleted", "Request removed.")
                else:
                    messagebox.showerror("Error", "Unable to delete this request (approved requests are kept for history).")
                self.show_requests()

            ctk.CTkButton(btns, text="View Details", width=140, command=lambda req=r: open_request_detail(req)).pack(
                anchor="e", padx=4, pady=(0, 6)
            )
            if r.get("status", "").lower() == "pending" and req_id:
                def cancel_request(req=req_id):
                    if not messagebox.askyesno("Cancel Request", "Cancel this adoption request?"):
                        return
                    try:
                        ok = self.controller.cancel_request(req, adopter_id=user_id)
                    except Exception as e:
                        messagebox.showerror("Error", f"Unable to cancel request.\n{e}")
                        return
                    if ok:
                        messagebox.showinfo("Cancelled", "Your adoption request has been cancelled.")
                    else:
                        messagebox.showerror("Error", "Unable to cancel this request (it may already be processed).")
                    self.show_requests()
                ctk.CTkButton(btns, text="Cancel", width=120, fg_color="#D64545", hover_color="#B53030",
                              command=cancel_request).pack(anchor="e", padx=4, pady=(0, 6))

            ctk.CTkButton(btns, text="Delete", width=120, fg_color="#4B5563", hover_color="#374151",
                          command=delete_request).pack(anchor="e", padx=4, pady=(0, 6))

    # --------------------------------------------------
    def show_notifications(self):
        self.clear()
        make_header(self.content, "Notifications", "Status updates and reminders.")

        hero = ctk.CTkFrame(self.content, fg_color="#00156A")
        hero.pack(fill="both", expand=True)

        ctk.CTkLabel(hero, text="Notifications", font=("Georgia", 44, "bold"), text_color="white").pack(
            pady=(22, 6)
        )
        ctk.CTkLabel(hero, text="All your request updates and reminders.", font=("Georgia", 16), text_color="#D4FAFF").pack(
            pady=(0, 18)
        )

        shell = ctk.CTkFrame(hero, width=1040, height=640, corner_radius=40, fg_color="#D4FAFF", border_width=2, border_color="#9EC9FF")
        shell.pack(fill="both", expand=True, padx=22, pady=(0, 26))
        shell.pack_propagate(False)

        container = ctk.CTkFrame(shell, fg_color="#D4FAFF")
        container.pack(fill="both", expand=True, padx=18, pady=18)

        toolbar = ctk.CTkFrame(container, fg_color="#D4FAFF")
        toolbar.pack(fill="x", padx=10, pady=(10, 0))

        user_id = self._get_user_id()
        if not user_id:
            messagebox.showerror("Error", "Cannot load notifications: adopter ID not found.")
            return

        try:
            notifications = self.controller.list_notifications(user_id)
        except Exception as e:
            messagebox.showerror("Error", f"Unable to fetch notifications.\n{e}")
            return

        def refresh():
            self.show_notifications()

        def mark_all():
            for note in notifications:
                try:
                    self.controller.mark_notification_read(note.get("id"))
                except Exception:
                    continue
            refresh()

        def clear_all():
            if not notifications:
                return
            if not messagebox.askyesno("Clear Notifications", "Remove all notifications?"):
                return
            try:
                self.controller.clear_notifications(user_id)
            except Exception as e:
                messagebox.showerror("Error", f"Unable to clear notifications.\n{e}")
                return
            refresh()

        ctk.CTkButton(toolbar, text="Refresh", width=120, fg_color="#0B84FF", hover_color="#0861BD",
                      text_color="white", command=refresh).pack(side="right", padx=6)
        ctk.CTkButton(toolbar, text="Mark All Read", width=140, fg_color="#1E63D1", hover_color="#174DA6",
                      text_color="white", command=mark_all).pack(side="right", padx=6)
        ctk.CTkButton(toolbar, text="Clear All", width=120, fg_color="#D64545", hover_color="#B53030",
                      text_color="white", command=clear_all).pack(side="right", padx=6)

        scroll = ctk.CTkScrollableFrame(container, fg_color="white")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        if not notifications:
            ctk.CTkLabel(scroll, text="No notifications yet.", font=("Georgia", 14), text_color="#666").pack(pady=14)
            return

        def mark_one(note_id):
            try:
                self.controller.mark_notification_read(note_id)
                refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Unable to mark notification.\n{e}")

        def remove_one(note_id):
            try:
                self.controller.delete_notification(note_id)
                refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Unable to remove notification.\n{e}")

        for note in notifications:
            bg = "#eef2ff" if not note.get("is_read") else "#f8fafc"
            card = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=12, border_width=1, border_color="#E5E7EB")
            card.pack(fill="x", padx=8, pady=6)

            ctk.CTkLabel(
                card,
                text=note.get("message", ""),
                font=("Georgia", 13),
                text_color="#111",
                wraplength=760,
                justify="left",
            ).pack(anchor="w", padx=12, pady=(10, 4))

            meta_text = f"Received: {note.get('created_at') or '—'}"
            ctk.CTkLabel(card, text=meta_text, font=("Georgia", 11), text_color="#555").pack(
                anchor="w", padx=12, pady=(0, 8)
            )

            btns = ctk.CTkFrame(card, fg_color=bg)
            btns.pack(anchor="e", padx=10, pady=(0, 10))

            if not note.get("is_read"):
                ctk.CTkButton(
                    btns,
                    text="Mark as Read",
                    width=130,
                    fg_color="#1E63D1",
                    hover_color="#174DA6",
                    command=lambda nid=note.get("id"): mark_one(nid),
                ).pack(side="left", padx=5)
            ctk.CTkButton(
                btns,
                text="Remove",
                width=110,
                fg_color="#D64545",
                hover_color="#B53030",
                command=lambda nid=note.get("id"): remove_one(nid),
            ).pack(side="left", padx=5)

    # --------------------------------------------------
    def show_history(self):
        self.clear()
        make_header(self.content, "Adoption History", "Your adopted pets and their details.")

        hero = ctk.CTkFrame(self.content, fg_color="#00156A")
        hero.pack(fill="both", expand=True)

        ctk.CTkLabel(hero, text="Adoption History", font=("Georgia", 44, "bold"), text_color="white").pack(
            pady=(22, 6)
        )
        ctk.CTkLabel(hero, text="All your approved adoptions with photos and details.", font=("Georgia", 16),
                     text_color="#D4FAFF").pack(pady=(0, 18))

        shell = ctk.CTkFrame(hero, width=1040, height=620, corner_radius=40, fg_color="#D4FAFF", border_width=2, border_color="#9EC9FF")
        shell.pack(fill="both", expand=True, padx=22, pady=(0, 26))
        shell.pack_propagate(False)

        toolbar = ctk.CTkFrame(shell, fg_color="#D4FAFF")
        toolbar.pack(fill="x", padx=26, pady=(18, 6))

        if not hasattr(self, "history_category_filter"):
            self.history_category_filter = "All"

        def set_history_filter(val):
            self.history_category_filter = val or "All"
            self.show_history()

        ctk.CTkLabel(toolbar, text="Category:", font=("Georgia", 13, "bold"), text_color="#00156A").pack(side="left", padx=(0, 8))
        cat_combo = ctk.CTkComboBox(
            toolbar,
            values=["All", "dog", "cat"],
            width=160,
            fg_color="#DDE1E6",
            button_color="#DDE1E6",
            text_color="black",
            command=set_history_filter,
        )
        try:
            cat_combo.set(self.history_category_filter)
        except Exception:
            cat_combo.set("All")
        cat_combo.pack(side="left", padx=(0, 12))

        table = ctk.CTkScrollableFrame(shell, fg_color="#D4FAFF")
        table.pack(fill="both", expand=True, padx=26, pady=(0, 22))

        user_id = self._get_user_id()
        try:
            hist = self.controller.adoption_history(user_id, self.history_category_filter)
        except Exception:
            hist = []

        if not hist:
            ctk.CTkLabel(table, text="No adoptions yet.", font=("Georgia", 14)).pack(pady=12)
            return

        def resolve_pet_image(photo_path, size=(140, 140)):
            """
            Try images/ then assets/, then absolute path for historical rows.
            Handles already-prefixed 'images/<file>' paths.
            """
            if not photo_path:
                return None
            normalized = photo_path.replace("\\", "/")
            if normalized.startswith("images/"):
                normalized = normalized.split("/", 1)[1]
            candidates = []
            if os.path.isabs(photo_path):
                candidates.append(photo_path)
            candidates.append(str(IMAGES_ROOT / normalized))
            candidates.append(str(ASSETS_ROOT / normalized))
            for path in candidates:
                if os.path.exists(path):
                    try:
                        return load_pet_image(path, size=size)
                    except Exception:
                        continue
            return None

        for h in hist:
            row = ctk.CTkFrame(table, fg_color="white", corner_radius=20, border_width=1, border_color="#b7d4ff")
            row.pack(fill="x", padx=10, pady=8)

            body = ctk.CTkFrame(row, fg_color="white")
            body.pack(fill="both", expand=True, padx=12, pady=12)

            pet_name = h.get("pet_name") or h.get("name") or "Unknown Pet"
            adopted = h.get("adopted_at") or h.get("date_requested") or ""
            desc = h.get("description") or "No description provided."
            category = h.get("category") or ""
            breed = h.get("breed") or ""
            age = h.get("age") or "N/A"
            sex = h.get("sex") or "N/A"
            vaccinated = h.get("vaccinated")
            vaccinated_txt = "Vaccinated" if str(vaccinated).lower() in ("1", "true", "yes") else "Not vaccinated"
            status = h.get("status") or ""
            photo = resolve_pet_image(h.get("photo_path"))

            img = ctk.CTkLabel(body, image=photo, text="No Image" if not photo else "")
            img.image = photo
            img.pack(side="left", padx=(0, 16), pady=6)

            info = ctk.CTkFrame(body, fg_color="white")
            info.pack(side="left", fill="both", expand=True)

            header = ctk.CTkFrame(info, fg_color="white")
            header.pack(fill="x")
            ctk.CTkLabel(header, text=pet_name, font=("Georgia", 23, "bold"), text_color="#0f172a").pack(side="left", anchor="w")

            status_lower = str(status).lower()
            badge_color = "#22C55E" if status_lower == "approved" else "#EAB308" if status_lower == "pending" else "#EF4444"
            ctk.CTkLabel(
                header,
                text=status.title() if status else "Status",
                font=("Georgia", 12, "bold"),
                text_color="white",
                fg_color=badge_color,
                corner_radius=12,
                padx=10,
                pady=4,
            ).pack(side="right", padx=(8, 0))

            meta_parts = [part for part in [category, breed] if part]
            meta = " • ".join(meta_parts) if meta_parts else "Pet details"
            ctk.CTkLabel(info, text=meta, font=("Georgia", 14), text_color="#334155").pack(anchor="w", pady=(6, 6))

            stats_row = ctk.CTkFrame(info, fg_color="white")
            stats_row.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(stats_row, text=f"Age: {age}", font=("Georgia", 13), text_color="#111").pack(side="left", padx=(0, 10))
            ctk.CTkLabel(stats_row, text=f"Sex: {sex}", font=("Georgia", 13), text_color="#111").pack(side="left", padx=(0, 10))
            ctk.CTkLabel(stats_row, text=vaccinated_txt, font=("Georgia", 12, "bold"), text_color="#0f172a").pack(side="left")

            ctk.CTkLabel(info, text=f"Adopted on: {adopted}", font=("Georgia", 12), text_color="#0f172a").pack(anchor="w", pady=(0, 6))
            ctk.CTkLabel(
                info,
                text=desc,
                font=("Georgia", 13),
                text_color="#1f2937",
                wraplength=760,
                justify="left",
            ).pack(anchor="w", pady=(6, 0))

    # --------------------------------------------------
    def show_profile(self):
        self.clear()
        make_header(self.content, "My Profile")

        wrapper = ctk.CTkFrame(self.content, fg_color="white")
        wrapper.pack(fill="both", expand=True, padx=18, pady=14)

        container = ctk.CTkFrame(wrapper, fg_color="white", corner_radius=20)
        container.pack(fill="both", expand=True)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=2)
        container.grid_rowconfigure(0, weight=1)

        user = self.app.current_user or {}
        user_id = self._get_user_id()

        # LEFT PANEL - Deep blue
        left = ctk.CTkFrame(container, fg_color="#1E3A8A", corner_radius=20)
        left.grid(row=0, column=0, sticky="nswe")

        image_path = user.get("photo_path") or user.get("image") or ""
        profile_img = None
        if image_path:
            try:
                path = image_path
                if not os.path.isabs(path):
                    path = os.path.join(IMAGES_ROOT, path)
                profile_img = load_pet_image(path, size=(180, 180))
            except Exception:
                profile_img = None

        img_holder = ctk.CTkFrame(left, width=200, height=200, fg_color="#0F1E4D", corner_radius=20)
        img_holder.pack(pady=40, padx=30)
        img_holder.pack_propagate(False)

        img_label = ctk.CTkLabel(img_holder, image=profile_img, text="No Image" if not profile_img else "")
        img_label.image = profile_img
        img_label.pack(expand=True)

        info_block = ctk.CTkFrame(left, fg_color="#1E3A8A")
        info_block.pack(pady=(0, 12))
        ctk.CTkLabel(
            info_block,
            text=user.get("name") or "Your Name",
            font=("Georgia", 20, "bold"),
            text_color="white",
        ).pack(anchor="center")
        ctk.CTkLabel(
            info_block,
            text=user.get("email") or "",
            font=("Georgia", 14),
            text_color="#dbeafe",
        ).pack(anchor="center", pady=(2, 0))
        phone_txt = user.get("phone") or user.get("phone_number") or ""
        if phone_txt:
            ctk.CTkLabel(
                info_block,
                text=phone_txt,
                font=("Georgia", 13),
                text_color="#cbd5f5",
            ).pack(anchor="center")

        img_entry = ctk.CTkEntry(left, width=220, placeholder_text="Profile Image Path")
        img_entry.insert(0, image_path)
        img_entry.pack(pady=(10, 5))

        def browse_photo():
            path = filedialog.askopenfilename(
                title="Select profile image",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp")]
            )
            if path:
                img_entry.delete(0, "end")
                img_entry.insert(0, path)

        def remove_photo():
            img_entry.delete(0, "end")

        btn_box = ctk.CTkFrame(left, fg_color="transparent")
        btn_box.pack(pady=10)
        ctk.CTkButton(btn_box, text="Browse", width=100, command=browse_photo).pack(side="left", padx=5)
        ctk.CTkButton(btn_box, text="Remove", width=100, fg_color="#D64545", hover_color="#B53030", command=remove_photo).pack(side="left", padx=5)

        # RIGHT PANEL - Light blue
        right = ctk.CTkFrame(container, fg_color="#E8F0FD", corner_radius=20)
        right.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(right, text="Account Information", font=("Georgia", 26, "bold"), text_color="#1E3A8A").pack(anchor="w", padx=40, pady=(40, 20))

        # Normalize displayed values (avoid showing "None" in inputs).
        age_val_raw = user.get("age")
        age_val = "" if age_val_raw in (None, "None") else str(age_val_raw)
        fields = [
            ("Full Name", "name", user.get("name") or ""),
            ("Age", "age", age_val),
            ("Email", "email", user.get("email") or ""),
            ("Phone Number", "phone", user.get("phone") or user.get("phone_number") or ""),
            ("Birthdate (YYYY-MM-DD)", "birthdate", user.get("birthdate") or ""),
        ]

        entries = {}
        for label, key, value in fields:
            ctk.CTkLabel(right, text=label, font=("Georgia", 14), text_color="#1E3A8A").pack(anchor="w", padx=40, pady=(8, 0))
            entry = ctk.CTkEntry(right, width=350)
            if value not in (None, ""):
                entry.insert(0, str(value))
            entries[key] = entry
            entry.pack(padx=40, pady=5)

        def save_profile():
            if not user_id:
                messagebox.showerror("Error", "Missing user id. Please log in again.")
                return
            photo_path = img_entry.get().strip()
            age_raw = entries["age"].get().strip()
            # Treat common "no value" inputs as empty
            if age_raw.lower() in ("none", "n/a", "na", "unknown"):
                age_raw = ""
            try:
                updated = self.controller.update_profile(
                    user_id,
                    entries["name"].get().strip(),
                    entries["email"].get().strip(),
                    entries["phone"].get().strip(),
                    entries["birthdate"].get().strip(),
                    photo_path,
                    age_raw,
                )
                self.app.current_user.update(updated)
                messagebox.showinfo("Saved", "Profile updated!")
                self.show_profile()
            except Exception as e:
                messagebox.showerror("Error", f"Unable to save profile.\n{e}")

        actions = ctk.CTkFrame(right, fg_color="#E8F0FD")
        actions.pack(fill="x", padx=30, pady=(20, 10))
        ctk.CTkButton(actions, text="Save Profile", fg_color="#1E40AF", hover_color="#1E3A8A", width=180, height=40, command=save_profile).pack(side="right", padx=(0, 8), pady=4)

        def delete_account():
            if not messagebox.askyesno("Delete Account", "Delete your adopter account? This cannot be undone."):
                return
            if not user_id:
                messagebox.showerror("Error", "Missing user id. Please log in again.")
                return
            img_path = user.get("photo_path") or user.get("image") or ""
            try:
                self.controller.delete_account(user_id, img_path)
                messagebox.showinfo("Deleted", "Your account was deleted.")
                self.app.logout()
            except Exception as e:
                messagebox.showerror("Error", f"Unable to delete account.\n{e}")

        ctk.CTkButton(actions, text="Delete Account", fg_color="#D64545", hover_color="#B53030", width=180, height=40, command=delete_account).pack(side="right", padx=(0, 8), pady=4)

    # --------------------------------------------------
    def show_help_center(self):
        self.clear()
        hero = ctk.CTkFrame(self.content, fg_color="#00156A")
        hero.pack(fill="both", expand=True)

        ctk.CTkLabel(hero, text="Help Center", font=("Georgia", 44, "bold"), text_color="white").pack(
            pady=(22, 6)
        )
        ctk.CTkLabel(hero, text="Find answers and guides below.", font=("Georgia", 16), text_color="#D4FAFF").pack(
            pady=(0, 18)
        )

        shell = ctk.CTkFrame(hero, width=1100, height=640, corner_radius=40, fg_color="#D4FAFF", border_width=2, border_color="#9EC9FF")
        shell.pack(fill="both", expand=True, padx=22, pady=(0, 26))
        shell.pack_propagate(False)

        layout = ctk.CTkFrame(shell, fg_color="#D4FAFF")
        layout.pack(fill="both", expand=True, padx=26, pady=22)

        nav = ctk.CTkFrame(layout, fg_color="white", corner_radius=22, width=240, height=380)
        nav.pack(side="left", fill="y", padx=(0, 26))
        nav.pack_propagate(False)

        ctk.CTkLabel(nav, text="Categories", font=("Georgia", 20, "bold"), text_color="#06215A").pack(pady=(18, 12))

        content_card = ctk.CTkFrame(layout, fg_color="white", corner_radius=22)
        content_card.pack(side="left", fill="both", expand=True)

        output = ctk.CTkTextbox(content_card, fg_color="white", text_color="black", font=("Georgia", 14), wrap="word")
        output.pack(fill="both", expand=True, padx=22, pady=22)

        def load_text(t):
            output.delete("0.0", "end")
            output.insert("0.0", t)

        def nav_btn(label, text):
            ctk.CTkButton(
                nav,
                text=label,
                width=180,
                height=42,
                fg_color="#1E63D1",
                hover_color="#174DA6",
                corner_radius=10,
                font=("Georgia", 14),
                command=lambda: load_text(text),
            ).pack(pady=8)

        nav_btn("FAQ", self.help_faq())
        nav_btn("Terms & Conditions", self.help_terms())
        nav_btn("Privacy Policy", self.help_privacy())

        load_text(self.help_faq())

    def help_faq(self):
        return (
            "Adopter FAQ\n\n"
            "Q: How do I start the adoption process?\n"
            "A: Go to the Available Pets section, choose a pet you're interested in, and click the 'Apply for Adoption' button.\n\n"
            "Q: Do I need an account to adopt a pet?\n"
            "A: Yes. You must log in or create an adopter account before submitting any adoption request.\n\n"
            "Q: What information do I need to provide when applying?\n"
            "A: You are required to fill out your name, address, contact number, birthdate, and your previous adoption experience.\n\n"
            "Q: What happens after I submit my adoption request?\n"
            "A: Your request will be reviewed by an administrator. You will receive a notification once your request is approved or declined.\n\n"
            "Q: How long does it take for approval?\n"
            "A: Processing time varies depending on the number of requests and the admin’s evaluation. Most requests are reviewed within 1–3 days.\n\n"
            "Q: Why was my request declined?\n"
            "A: Decline reasons vary. Some admins include a specific reason. Common reasons include incomplete information, unsuitable environment, or conflicts with pet requirements.\n\n"
            "Q: Can I cancel my adoption request?\n"
            "A: Yes. You can cancel your request anytime as long as it is still marked as 'Pending'. Once approved, cancellation may no longer be allowed.\n\n"
            "Q: Where can I see my submitted requests?\n"
            "A: Go to the 'My Requests' page located in your menu. All your pending, approved, and declined requests are displayed there.\n\n"
            "Q: How do I know if my request was approved?\n"
            "A: You will receive an in-app notification. You may also check your request status under the 'My Requests' page.\n\n"
            "Q: Can I edit my personal information?\n"
            "A: Yes. Go to your 'Profile' page to update your name, phone number, birthdate, address, or adoption experience details.\n\n"
            "Q: What should I do after my request is approved?\n"
            "A: The admin will contact you for the next steps, including meeting schedules, requirements, or pet pickup arrangements.\n\n"
            "Q: Will my personal information be safe?\n"
            "A: Yes. All information is securely stored in our system and used only for adoption-related purposes.\n\n"
            "Q: Who can I contact for further help?\n"
            "A: You may use the 'Help & Support' section or message the admin directly if available in your app.\n"
        )

    def help_terms(self):
        return (
            "Terms & Conditions\n\n"
            "Welcome to FurEver Home. By continuing to use this system, all administrators acknowledge and "
            "agree to follow the guidelines governing the management of adopter data, pet records, adoption "
            "requests, notifications, and system operations. These terms ensure transparency, safety, and "
            "ethical use of the platform.\n\n"

            "1. Accuracy of Information\n"
            "Administrators are responsible for ensuring all data entered into the system—including pet details, "
            "adopter profiles, medical information, and adoption histories—is complete and accurate. Any outdated "
            "or incorrect information must be corrected immediately to avoid confusion and misuse.\n\n"

            "2. Proper Screening of Adoption Requests\n"
            "Admins must carefully evaluate every adoption request before approving or declining it. Evaluations "
            "should consider the adopter’s experience, readiness, living conditions, and the pet’s needs. Decisions "
            "must always prioritize the welfare, safety, and compatibility of the pet and adopter.\n\n"

            "3. Responsible Use of Administrative Privileges\n"
            "Admin access is a privilege and must not be used to alter, hide, destroy, or manipulate records for "
            "personal reasons. All actions taken inside the system must be legitimate, transparent, and aligned with "
            "official procedures. Unauthorized modification of adoption outcomes, pet availability, or system "
            "permissions is strictly prohibited.\n\n"

            "4. Data Privacy and Confidentiality\n"
            "Adopter information—including contact details, address, birthdate, and adoption history—is confidential "
            "and must be protected at all times. These details may only be used for adoption-related purposes and may "
            "not be disclosed or shared without proper consent. Admins are expected to follow basic data privacy "
            "protocols to prevent breaches and unauthorized access.\n\n"

            "5. Ethical Handling of Pet Records\n"
            "Pet profiles must accurately represent their true condition, behavior, medical status, and adoption "
            "availability. Misrepresenting age, breed, temperament, or health is not allowed. Pets marked as adopted "
            "must reflect real adoption status to avoid duplicate requests or misinformation.\n\n"

            "6. System Security and Account Protection\n"
            "Admins are responsible for safeguarding their login credentials. Passwords must not be shared with "
            "anyone under any circumstances. Any suspicious activity, unauthorized login attempts, or system "
            "irregularities must be reported immediately to maintain platform integrity.\n\n"

            "7. Integrity in Decision-Making\n"
            "All decisions made within the system—such as approving or rejecting adoption requests—must be fair, free "
            "from bias, and based solely on documented facts. Personal conflicts, favoritism, or discrimination must "
            "never influence administrative actions.\n\n"

            "8. Restrictions on Data Removal\n"
            "Admins may not remove pet profiles, adoption records, or user accounts unless authorized and justified. "
            "Deletion of important data for personal benefit or to conceal errors is strictly forbidden.\n\n"

            "9. Proper Communication and Feedback\n"
            "When declining adoption requests, admins are encouraged to provide clear, constructive, and respectful "
            "feedback so adopters understand the reason behind the decision. Communication must remain professional.\n\n"

            "10. System Updates and Features\n"
            "Admins must comply with any changes, updates, or new policies added to the system. System improvements "
            "may introduce new rules that administrators must adhere to.\n\n"

            "11. Accountability for Misuse\n"
            "Any abuse of administrative powers—such as unauthorized edits, tampering with records, or mishandling "
            "sensitive data—may result in revoked access, disciplinary action, or removal of admin privileges.\n\n"

            "12. Acceptance of Terms\n"
            "By using the FurEver Home system, administrators confirm they understand and accept all terms stated "
            "above. Continued system use implies ongoing agreement to these policies and future revisions.\n"
        )

    def help_privacy(self):
        return (
            "Privacy Policy\n\n"
            "This Privacy Policy describes how FurEver Home collects, uses, stores, and protects the "
            "personal information of both Adopters and Administrators who use the system.\n\n"
            "1. Information We Collect\n"
            "   • Adopter Information: name, address, email, phone number, birthdate, and adoption history.\n"
            "   • Admin Information: name, email, phone number, and profile details used for system management.\n"
            "   • System Activity: login records, request submissions, approval/decline actions.\n"
            "   • Pet Information: details added or updated by admins for adoption listings.\n\n"
            "2. How We Use Your Data\n"
            "The information collected is used solely for:\n"
            "   • Processing adoption requests\n"
            "   • Verifying adopter identity and readiness\n"
            "   • Sending notifications about request status updates\n"
            "   • Maintaining accurate adoption history\n"
            "   • Improving system performance and security\n"
            "   • Ensuring the safety and welfare of animals under the organization\n\n"
            "3. Storage & Security Measures\n"
            "   • All personal data is securely stored within the FurEver Home database.\n"
            "   • Access is restricted based on user role (Admin / Adopter).\n"
            "   • Passwords must be kept private and are not visible to staff.\n"
            "   • Security measures are applied to prevent unauthorized access, data leaks, and misuse.\n\n"
            "4. Information Sharing\n"
            "We do not sell or share any user data. Information may only be shared in the following cases:\n"
            "   • Adoption verification steps required by the organization\n"
            "   • Legal requests or compliance with authorities\n"
            "   • When adopter details are needed to finalize an adoption\n"
            "   • Internal record keeping for monitoring and transparency\n\n"
            "5. User Rights\n"
            "Users of the system have the right to:\n"
            "   • Request correction of incorrect or outdated information\n"
            "   • Review their submitted adoption details\n"
            "   • Receive updates regarding the status of their adoption requests\n"
            "   • Ask for clarification about how their data is used\n\n"
            "6. Data Retention\n"
            "   • Adoption records and related information are stored only as long as needed for system "
            "     operations and historical tracking.\n"
            "   • Inactive accounts or data may be archived but will remain protected.\n\n"
            "7. Protection of Minors\n"
            "FurEver Home may restrict adoption activities for minors. Personal data of users below the "
            "required age will not be collected without proper verification.\n\n"
            "8. Consent\n"
            "By using FurEver Home, users agree to the collection and use of their information as described "
            "in this Privacy Policy. Continued use of the system signifies acceptance of these practices.\n"
        )

    def _download_adoption_form(self, request_row, status_raw):
        """
        Generate and save a stamped adoption form PNG.
        """
        pet_name = request_row.get("pet_name") or "Unknown Pet"
        adopter_name = request_row.get("adopter_name") or self.user.get("name", "")
        note = request_row.get("reason", "")
        created = request_row.get("created_at") or request_row.get("requested_at") or ""
        status_label = "APPROVED" if status_raw == "approved" else "REJECTED"
        pet_photo = request_row.get("pet_image_resolved") or request_row.get("pet_photo") or request_row.get("pet_image")
        adopter_photo = request_row.get("adopter_photo") or (self.user or {}).get("photo_path")

        # Attempt to parse individual fields from the note for nicer layout
        def parse_note(note_text):
            info = {}
            if not note_text:
                return info
            for line in note_text.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    info[key.strip().lower()] = val.strip()
            return info

        parsed = parse_note(note)
        full_name = parsed.get("full name", adopter_name)
        email = parsed.get("email", "")
        phone = parsed.get("phone", "")
        address = parsed.get("address", "")
        experience = parsed.get("experience caring for pets") or parsed.get("have prior experience with pet care or adoption") or "N/A"
        how_many = parsed.get("how many (if yes)") or parsed.get("if yes, how many") or "N/A"
        reason_text = parsed.get("reason") or parsed.get("reason for adoption") or "N/A"
        pet_category = request_row.get("category") or ""
        pet_breed = request_row.get("breed") or ""
        pet_age = request_row.get("age") or ""
        pet_sex = request_row.get("sex") or ""
        vaccinated_val = request_row.get("vaccinated")
        vaccinated_txt = "Yes" if str(vaccinated_val).strip().lower() in ("1", "true", "yes") else "No/Unknown"

        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"adoption_form_{pet_name.replace(' ', '_')}.pdf",
            title="Save Adoption Form",
        )
        if not save_path:
            return

        template_pdf = ASSETS_ROOT / "Adoption-Form-Final.pdf"
        if not template_pdf.exists():
            messagebox.showerror("Template missing", "Adoption-Form-Final.pdf not found in assets.")
            return

        try:
            from shutil import copyfile

            copyfile(template_pdf, save_path)
        except Exception as e:
            messagebox.showerror("Save failed", f"Could not save the adoption form.\n\n{e}")
            return

        messagebox.showinfo("Saved", f"Adoption form saved to:\n{save_path}")

    # --------------------------------------------------
    def show_about(self):
        self.clear()
        hero = ctk.CTkFrame(self.content, fg_color="#00156A")
        hero.pack(fill="both", expand=True)

        ctk.CTkLabel(hero, text="About / Rate Us", font=("Georgia", 44, "bold"), text_color="white").pack(
            pady=(22, 6)
        )
        ctk.CTkLabel(hero, text="Meet the team behind FurEver Home.", font=("Georgia", 16), text_color="#D4FAFF").pack(
            pady=(0, 18)
        )

        shell = ctk.CTkFrame(hero, width=1100, height=640, corner_radius=40, fg_color="#D4FAFF", border_width=2, border_color="#9EC9FF")
        shell.pack(fill="both", expand=True, padx=22, pady=(0, 26))
        shell.pack_propagate(False)

        scroll = ctk.CTkScrollableFrame(shell, fg_color="#D4FAFF", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        admins_card = ctk.CTkFrame(scroll, fg_color="white", corner_radius=25)
        admins_card.pack(fill="x", pady=20)
        ctk.CTkLabel(admins_card, text="Our Admins", font=("Georgia", 26, "bold"), text_color="#06215A").pack(
            anchor="w", padx=25, pady=(20, 10)
        )

        try:
            admins = self.controller.admin_profiles()
        except Exception:
            admins = []

        images_dir = IMAGES_ROOT
        base_dir = PROJECT_ROOT

        def load_icon(fname, size=(22, 22)):
            path = ASSETS_ROOT / fname
            if not path.exists():
                return None
            try:
                return ctk.CTkImage(Image.open(path).convert("RGBA"), size=size)
            except Exception:
                return None

        fb_icon = getattr(self, "fb_icon", None) or load_icon("fb.png")
        ig_icon = getattr(self, "ig_icon", None) or load_icon("ig.png")
        self.fb_icon = fb_icon
        self.ig_icon = ig_icon

        def load_photo(path_value, size=(70, 70)):
            if not path_value:
                return None
            candidates = []
            if os.path.isabs(path_value):
                candidates.append(path_value)
            else:
                candidates.append(os.path.join(images_dir, path_value))
                candidates.append(os.path.join(base_dir, path_value))
            for path in candidates:
                if not os.path.exists(path):
                    continue
                try:
                    return ctk.CTkImage(Image.open(path).convert("RGBA"), size=size)
                except Exception:
                    continue
            return None

        fallback_photos = {
            "Angelica C. Corpuz": load_photo("angelica.jpg"),
            "Ronin Jacob C. Guevarra": load_photo("ronin.jpg"),
            "Francine Anne M. Villaraza": load_photo("francine.jpg"),
        }

        icon_map = {
            "fb": fb_icon,
            "facebook": fb_icon,
            "ig": ig_icon,
            "instagram": ig_icon,
        }

        def add_link(parent, icon, text, url):
            row = ctk.CTkFrame(parent, fg_color="#f2f5fa")
            row.pack(anchor="w", padx=15, pady=2)
            if icon:
                icon_lbl = ctk.CTkLabel(row, image=icon, text="")
                icon_lbl.image = icon
                icon_lbl.pack(side="left", padx=(0, 6))
            link = ctk.CTkLabel(
                row,
                text=text,
                font=("Georgia", 13, "bold"),
                text_color="#0a3d91",
                cursor="hand2",
            )
            link.pack(side="left")
            link.bind("<Button-1>", lambda _e=None, u=url: webbrowser.open_new(u))

        if not admins:
            ctk.CTkLabel(admins_card, text="No admin profiles yet.", font=("Georgia", 14), text_color="#777").pack(
                padx=25, pady=(0, 14), anchor="w"
            )

        for admin in admins:
            entry = ctk.CTkFrame(admins_card, fg_color="#f2f5fa", corner_radius=15)
            entry.pack(fill="x", padx=25, pady=10)

            row = ctk.CTkFrame(entry, fg_color="#f2f5fa")
            row.pack(fill="x", padx=10, pady=6)

            name = admin.get("name") or "Unknown"
            links = []
            fb = admin.get("facebook_url") or admin.get("facebook")
            ig = admin.get("instagram_url") or admin.get("instagram")
            if fb:
                links.append(("Facebook", fb, "fb"))
            if ig:
                links.append(("Instagram", ig, "ig"))

            photo = load_photo(admin.get("photo_path")) or fallback_photos.get(name)
            if photo:
                img_lbl = ctk.CTkLabel(row, image=photo, text="")
                img_lbl.image = photo
                img_lbl.pack(side="left", padx=(4, 12), pady=6)

            content = ctk.CTkFrame(row, fg_color="#f2f5fa")
            content.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(content, text=name, font=("Georgia", 17, "bold"), text_color="#06215A").pack(
                anchor="w", pady=(0, 4)
            )
            for label, url, icon_key in links:
                if not url:
                    continue
                add_link(content, icon_map.get((icon_key or "").lower()), label, url)

        rate_card = ctk.CTkFrame(scroll, fg_color="white", corner_radius=22)
        rate_card.pack(fill="x", pady=16)
        ctk.CTkLabel(rate_card, text="Rate Us", font=("Georgia", 24, "bold"), text_color="#06215A").pack(pady=(18, 6))
        stars_frame = ctk.CTkFrame(rate_card, fg_color="white")
        stars_frame.pack(pady=10)
        rating_var = ctk.StringVar(value="0")

        def rate(n):
            rating_var.set(str(n))
            messagebox.showinfo("Thank you!", f"You rated us {n} stars!")
            try:
                self.controller.notify_admins_rating(n)
            except Exception:
                pass

        for i in range(1, 6):
            ctk.CTkButton(
                stars_frame,
                text="?",
                width=52,
                height=44,
                fg_color="#1E63D1",
                hover_color="#174DA6",
                corner_radius=10,
                font=("Georgia", 20),
                command=lambda x=i: rate(x),
            ).pack(side="left", padx=5)

        about_card = ctk.CTkFrame(scroll, fg_color="white", corner_radius=25)
        about_card.pack(fill="x", pady=20)

        about_logo = getattr(self, "about_logo", None) or load_icon("FurEver_Home_Logo.png", size=(80, 80))
        self.about_logo = about_logo

        header_row = ctk.CTkFrame(about_card, fg_color="white")
        header_row.pack(fill="x", padx=18, pady=(18, 8))
        if about_logo:
            logo_lbl = ctk.CTkLabel(header_row, image=about_logo, text="")
            logo_lbl.image = about_logo
            logo_lbl.pack(side="left", padx=(6, 14))
        ctk.CTkLabel(header_row, text="About FurEver Home", font=("Georgia", 24, "bold"), text_color="#06215A").pack(
            side="left", pady=4
        )

        about_text = (
            "FurEver Home is a community-driven pet adoption platform designed to make the adoption process simple, "
            "transparent, and accessible for everyone. Our system connects loving adopters with pets in need of safe and permanent homes.\n\n"
            "Through our platform, adopters can browse available pets, submit applications, track their status, and receive "
            "updates directly from our administrators.\n\n"
            "FurEver Home helps shelters promote responsible pet ownership and ensures every pet finds the family they deserve. "
            "If you have questions or concerns, feel free to reach out to our administrators.\n\n"
            "Together, we can give every pet a chance at a FurEver Home."
        )

        ctk.CTkLabel(
            about_card,
            text=about_text,
            font=("Georgia", 18),
            text_color="#444",
            justify="center",
            wraplength=850,
        ).pack(anchor="center", padx=40, pady=(0, 22))
