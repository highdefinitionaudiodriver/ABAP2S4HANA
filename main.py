"""
SAP ECC to S/4HANA Migration Tool
A GUI application that converts ABAP code for S/4HANA compatibility (59 languages supported)
"""
import os
import sys
import threading
import traceback
import argparse
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from datetime import datetime

# Support running as script or frozen exe
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

from src.abap_parser import AbapParser, parse_abap_file
from src.s4_transformer import S4Transformer, MigrationOptions
from src.abap_generator import AbapCodeGenerator, BackupManager
from src.report_generator import ReportGenerator
from src.i18n import I18n, LANGUAGES


class AbapToS4App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.i18n = I18n("en")  # Default: English
        self.root.geometry("900x800")
        self.root.minsize(780, 660)
        self.root.resizable(True, True)

        self.is_running = False
        self.cancel_flag = False

        # Store widget references for language switching
        self._widgets = {}

        self._setup_styles()
        self._build_ui()
        self._apply_language()

    def _t(self, key: str, **kwargs) -> str:
        return self.i18n.t(key, **kwargs)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground="#2c3e50")
        style.configure("Header.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Run.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"))

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Top bar: Title + Language selector ---
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        self._widgets["title"] = ttk.Label(top_frame, style="Title.TLabel")
        self._widgets["title"].pack(side=tk.LEFT)

        # Language selector (right side)
        lang_frame = ttk.Frame(top_frame)
        lang_frame.pack(side=tk.RIGHT)

        self._widgets["lang_label"] = ttk.Label(lang_frame)
        self._widgets["lang_label"].pack(side=tk.LEFT, padx=(0, 4))

        self.lang_var = tk.StringVar(value="en")
        lang_display = [f"{v}" for v in LANGUAGES.values()]
        lang_codes = list(LANGUAGES.keys())
        self._lang_code_map = dict(zip(lang_display, lang_codes))

        lang_combo = ttk.Combobox(
            lang_frame, textvariable=tk.StringVar(value="English"),
            values=lang_display, width=12, state="readonly"
        )
        lang_combo.pack(side=tk.LEFT)
        lang_combo.bind("<<ComboboxSelected>>", lambda e: self._on_language_change(
            self._lang_code_map.get(lang_combo.get(), "en")
        ))
        self._widgets["lang_combo"] = lang_combo

        # --- Folder Selection ---
        self._widgets["folder_frame"] = ttk.LabelFrame(main_frame, padding=10)
        self._widgets["folder_frame"].pack(fill=tk.X, pady=(0, 8))
        folder_frame = self._widgets["folder_frame"]

        self._widgets["input_label"] = ttk.Label(folder_frame, style="Header.TLabel")
        self._widgets["input_label"].grid(row=0, column=0, sticky=tk.W, pady=2)

        self.input_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.input_var, width=60).grid(
            row=0, column=1, padx=5, pady=2, sticky=tk.EW
        )
        self._widgets["browse_input"] = ttk.Button(folder_frame, command=self._browse_input)
        self._widgets["browse_input"].grid(row=0, column=2, padx=2, pady=2)

        self._widgets["output_label"] = ttk.Label(folder_frame, style="Header.TLabel")
        self._widgets["output_label"].grid(row=1, column=0, sticky=tk.W, pady=2)

        self.output_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.output_var, width=60).grid(
            row=1, column=1, padx=5, pady=2, sticky=tk.EW
        )
        self._widgets["browse_output"] = ttk.Button(folder_frame, command=self._browse_output)
        self._widgets["browse_output"].grid(row=1, column=2, padx=2, pady=2)

        folder_frame.columnconfigure(1, weight=1)

        # --- Options ---
        self._widgets["options_frame"] = ttk.LabelFrame(main_frame, padding=10)
        self._widgets["options_frame"].pack(fill=tk.X, pady=(0, 8))
        options_frame = self._widgets["options_frame"]

        # Left column
        left_opts = ttk.Frame(options_frame)
        left_opts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Source Version
        src_frame = ttk.Frame(left_opts)
        src_frame.pack(fill=tk.X, pady=2)
        self._widgets["src_version_label"] = ttk.Label(src_frame)
        self._widgets["src_version_label"].pack(side=tk.LEFT)
        self.source_version_var = tk.StringVar(value="ECC 6.08")
        ttk.Combobox(
            src_frame, textvariable=self.source_version_var, width=18,
            values=["ECC 6.0", "ECC 6.04", "ECC 6.05", "ECC 6.06", "ECC 6.07", "ECC 6.08"],
            state="readonly"
        ).pack(side=tk.LEFT, padx=5)

        # Target Version
        tgt_frame = ttk.Frame(left_opts)
        tgt_frame.pack(fill=tk.X, pady=2)
        self._widgets["tgt_version_label"] = ttk.Label(tgt_frame)
        self._widgets["tgt_version_label"].pack(side=tk.LEFT)
        self.target_version_var = tk.StringVar(value="S/4HANA 2023")
        ttk.Combobox(
            tgt_frame, textvariable=self.target_version_var, width=18,
            values=["S/4HANA 1709", "S/4HANA 1809", "S/4HANA 1909",
                    "S/4HANA 2020", "S/4HANA 2021", "S/4HANA 2022", "S/4HANA 2023"],
            state="readonly"
        ).pack(side=tk.LEFT, padx=5)

        # Encoding
        enc_frame = ttk.Frame(left_opts)
        enc_frame.pack(fill=tk.X, pady=2)
        self._widgets["enc_label"] = ttk.Label(enc_frame)
        self._widgets["enc_label"].pack(side=tk.LEFT)
        self.encoding_var = tk.StringVar(value="utf-8")
        ttk.Combobox(
            enc_frame, textvariable=self.encoding_var, width=15,
            values=["utf-8", "shift_jis", "euc-jp", "cp932", "iso-8859-1", "cp1252", "ascii"],
            state="readonly"
        ).pack(side=tk.LEFT, padx=5)

        # File Extensions
        ext_frame = ttk.Frame(left_opts)
        ext_frame.pack(fill=tk.X, pady=2)
        self._widgets["ext_label"] = ttk.Label(ext_frame)
        self._widgets["ext_label"].pack(side=tk.LEFT)
        self.extensions_var = tk.StringVar(value=".abap,.txt,.prog,.ABAP")
        ttk.Entry(ext_frame, textvariable=self.extensions_var, width=30).pack(side=tk.LEFT, padx=5)

        # SAP Module Filter
        module_frame = ttk.Frame(left_opts)
        module_frame.pack(fill=tk.X, pady=2)
        self._widgets["module_label"] = ttk.Label(module_frame)
        self._widgets["module_label"].pack(side=tk.LEFT)

        self.module_var = tk.StringVar(value="ALL")
        self._module_options = ["ALL", "FI/CO", "MM", "SD", "BP", "PP", "ABAP Language"]
        self._widgets["module_combo"] = ttk.Combobox(
            module_frame, textvariable=self.module_var, width=18,
            values=self._module_options, state="readonly"
        )
        self._widgets["module_combo"].pack(side=tk.LEFT, padx=5)

        # Report Format
        report_frame = ttk.Frame(left_opts)
        report_frame.pack(fill=tk.X, pady=2)
        self._widgets["report_fmt_label"] = ttk.Label(report_frame)
        self._widgets["report_fmt_label"].pack(side=tk.LEFT)
        self.report_format_var = tk.StringVar(value="Both")
        ttk.Combobox(
            report_frame, textvariable=self.report_format_var, width=10,
            values=["HTML", "CSV", "Both"], state="readonly"
        ).pack(side=tk.LEFT, padx=5)

        # Right column - checkboxes
        right_opts = ttk.Frame(options_frame)
        right_opts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0))

        self.modernize_syntax_var = tk.BooleanVar(value=True)
        self._widgets["cb_modernize"] = ttk.Checkbutton(right_opts, variable=self.modernize_syntax_var)
        self._widgets["cb_modernize"].pack(anchor=tk.W, pady=1)

        self.convert_tables_var = tk.BooleanVar(value=True)
        self._widgets["cb_tables"] = ttk.Checkbutton(right_opts, variable=self.convert_tables_var)
        self._widgets["cb_tables"].pack(anchor=tk.W, pady=1)

        self.convert_bapis_var = tk.BooleanVar(value=True)
        self._widgets["cb_bapis"] = ttk.Checkbutton(right_opts, variable=self.convert_bapis_var)
        self._widgets["cb_bapis"].pack(anchor=tk.W, pady=1)

        self.convert_fm_var = tk.BooleanVar(value=True)
        self._widgets["cb_fm"] = ttk.Checkbutton(right_opts, variable=self.convert_fm_var)
        self._widgets["cb_fm"].pack(anchor=tk.W, pady=1)

        self.generate_report_var = tk.BooleanVar(value=True)
        self._widgets["cb_report"] = ttk.Checkbutton(right_opts, variable=self.generate_report_var)
        self._widgets["cb_report"].pack(anchor=tk.W, pady=1)

        self.add_comments_var = tk.BooleanVar(value=True)
        self._widgets["cb_comments"] = ttk.Checkbutton(right_opts, variable=self.add_comments_var)
        self._widgets["cb_comments"].pack(anchor=tk.W, pady=1)

        self.backup_var = tk.BooleanVar(value=True)
        self._widgets["cb_backup"] = ttk.Checkbutton(right_opts, variable=self.backup_var)
        self._widgets["cb_backup"].pack(anchor=tk.W, pady=1)

        # --- Action Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 8))

        self._widgets["run_btn"] = ttk.Button(
            button_frame, command=self._start_conversion,
            style="Run.TButton", width=20
        )
        self._widgets["run_btn"].pack(side=tk.LEFT, padx=5)
        self.run_button = self._widgets["run_btn"]

        self._widgets["cancel_btn"] = ttk.Button(
            button_frame, command=self._cancel_conversion,
            state=tk.DISABLED, width=12
        )
        self._widgets["cancel_btn"].pack(side=tk.LEFT, padx=5)
        self.cancel_button = self._widgets["cancel_btn"]

        self._widgets["clear_btn"] = ttk.Button(
            button_frame, command=self._clear_log, width=12
        )
        self._widgets["clear_btn"].pack(side=tk.RIGHT, padx=5)

        # --- Progress ---
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 4))

        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, mode="determinate"
        ).pack(fill=tk.X, side=tk.LEFT, expand=True)

        self.status_var = tk.StringVar()
        ttk.Label(progress_frame, textvariable=self.status_var, width=30).pack(side=tk.RIGHT, padx=5)

        # --- Log Output ---
        self._widgets["log_frame"] = ttk.LabelFrame(main_frame, padding=5)
        self._widgets["log_frame"].pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            self._widgets["log_frame"], wrap=tk.WORD, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
            selectbackground="#264f78"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.log_text.tag_configure("info", foreground="#4ec9b0")
        self.log_text.tag_configure("success", foreground="#6a9955")
        self.log_text.tag_configure("warning", foreground="#dcdcaa")
        self.log_text.tag_configure("error", foreground="#f44747")
        self.log_text.tag_configure("header", foreground="#569cd6", font=("Consolas", 9, "bold"))

    def _apply_language(self):
        """Apply current language to all widgets."""
        t = self._t

        self.root.title(t("app_title"))
        self._widgets["title"].configure(text=t("app_heading"))
        self._widgets["lang_label"].configure(text=t("language_label"))

        # Folders
        self._widgets["folder_frame"].configure(text=t("folders_frame"))
        self._widgets["input_label"].configure(text=t("input_folder_label"))
        self._widgets["output_label"].configure(text=t("output_folder_label"))
        self._widgets["browse_input"].configure(text=t("browse_button"))
        self._widgets["browse_output"].configure(text=t("browse_button"))

        # Options
        self._widgets["options_frame"].configure(text=t("options_frame"))
        self._widgets["src_version_label"].configure(text=t("source_version_label"))
        self._widgets["tgt_version_label"].configure(text=t("target_version_label"))
        self._widgets["enc_label"].configure(text=t("encoding_label"))
        self._widgets["ext_label"].configure(text=t("extensions_label"))
        self._widgets["module_label"].configure(text=t("module_filter_label"))
        self._widgets["report_fmt_label"].configure(text=t("report_format_label"))

        # Checkboxes
        self._widgets["cb_modernize"].configure(text=t("opt_modernize_syntax"))
        self._widgets["cb_tables"].configure(text=t("opt_convert_tables"))
        self._widgets["cb_bapis"].configure(text=t("opt_convert_bapis"))
        self._widgets["cb_fm"].configure(text=t("opt_convert_fm"))
        self._widgets["cb_report"].configure(text=t("opt_generate_report"))
        self._widgets["cb_comments"].configure(text=t("opt_add_comments"))
        self._widgets["cb_backup"].configure(text=t("opt_backup_originals"))

        # Buttons
        self._widgets["run_btn"].configure(text=t("convert_button"))
        self._widgets["cancel_btn"].configure(text=t("cancel_button"))
        self._widgets["clear_btn"].configure(text=t("clear_log_button"))

        # Status
        if not self.is_running:
            self.status_var.set(t("status_ready"))

        # Log frame
        self._widgets["log_frame"].configure(text=t("log_frame"))

    def _on_language_change(self, lang_code: str):
        self.i18n.lang = lang_code
        self._apply_language()

    def _browse_input(self):
        folder = filedialog.askdirectory(title=self._t("browse_input_title"))
        if folder:
            self.input_var.set(folder)

    def _browse_output(self):
        folder = filedialog.askdirectory(title=self._t("browse_output_title"))
        if folder:
            self.output_var.set(folder)

    def _clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)

    def _log(self, message: str, tag: str = "info"):
        self.log_text.configure(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)

    def _build_options(self) -> MigrationOptions:
        """Build MigrationOptions from the current GUI state."""
        # Parse SAP module filter
        module_sel = self.module_var.get()
        if module_sel == "ALL":
            sap_modules = ["ALL"]
        elif module_sel == "FI/CO":
            sap_modules = ["FI", "CO"]
        elif module_sel == "ABAP Language":
            sap_modules = ["ABAP"]
        else:
            sap_modules = [module_sel]

        extensions = [e.strip() for e in self.extensions_var.get().split(",")]

        return MigrationOptions(
            source_version=self.source_version_var.get(),
            target_version=self.target_version_var.get(),
            sap_modules=sap_modules,
            encoding=self.encoding_var.get(),
            extensions=extensions,
            modernize_syntax=self.modernize_syntax_var.get(),
            convert_tables=self.convert_tables_var.get(),
            convert_bapis=self.convert_bapis_var.get(),
            convert_fm=self.convert_fm_var.get(),
            generate_report=self.generate_report_var.get(),
            add_comments=self.add_comments_var.get(),
            backup_originals=self.backup_var.get(),
            report_format=self.report_format_var.get(),
        )

    def _start_conversion(self):
        t = self._t
        input_dir = self.input_var.get().strip()
        output_dir = self.output_var.get().strip()

        if not input_dir:
            messagebox.showwarning(t("warn_title"), t("warn_no_input"))
            return
        if not output_dir:
            messagebox.showwarning(t("warn_title"), t("warn_no_output"))
            return
        if not os.path.isdir(input_dir):
            messagebox.showerror(t("error_title"), t("error_no_input_dir", path=input_dir))
            return

        self.is_running = True
        self.cancel_flag = False
        self.run_button.configure(state=tk.DISABLED)
        self.cancel_button.configure(state=tk.NORMAL)
        self.progress_var.set(0)

        thread = threading.Thread(target=self._run_conversion, args=(input_dir, output_dir), daemon=True)
        thread.start()

    def _cancel_conversion(self):
        self.cancel_flag = True
        self._log(self._t("log_cancel_request"), "warning")

    def _run_conversion(self, input_dir: str, output_dir: str):
        t = self._t
        try:
            self._log("=" * 60, "header")
            self._log(t("log_starting"), "header")
            self._log("=" * 60, "header")
            self._log(t("log_input", path=input_dir))
            self._log(t("log_output", path=output_dir))

            options = self._build_options()

            extensions = options.extensions
            abap_files = []
            for root_dir, dirs, files in os.walk(input_dir):
                for f in files:
                    if any(f.endswith(ext) for ext in extensions):
                        abap_files.append(os.path.join(root_dir, f))

            if not abap_files:
                self._log(t("log_no_files", ext=str(extensions)), "warning")
                self._finish()
                return

            self._log(t("log_found_files", count=len(abap_files)), "info")
            self._log(t("log_source_version", version=options.source_version), "info")
            self._log(t("log_target_version", version=options.target_version), "info")
            self._log(t("log_module_filter", modules=", ".join(options.sap_modules)), "info")

            parser = AbapParser(encoding=options.encoding)
            transformer = S4Transformer(options)
            generator = AbapCodeGenerator(options)
            report_gen = ReportGenerator(options) if options.generate_report else None

            success_count = 0
            error_count = 0
            total_auto = 0
            total_review = 0
            total_manual = 0
            all_results = []  # (source_path, TransformResult)

            for i, filepath in enumerate(abap_files):
                if self.cancel_flag:
                    self._log(t("log_cancelled"), "warning")
                    break

                rel_path = os.path.relpath(filepath, input_dir)
                filename = os.path.basename(filepath)
                display_name = rel_path if os.path.dirname(rel_path) else filename
                progress = ((i + 1) / len(abap_files)) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(0, lambda f=display_name: self.status_var.set(
                    t("status_processing", file=f)
                ))

                self._log(f"\n{t('log_processing', file=display_name)}", "header")

                try:
                    # 1. Parse
                    self._log(t("log_parsing"), "info")
                    program = parser.parse_file(filepath)

                    self._log(t("log_report_name", name=program.report_name or "(unknown)"))
                    self._log(t("log_total_lines", count=program.total_lines))
                    self._log(t("log_tables_detected", count=len(program.tables_used)))
                    self._log(t("log_fm_detected", count=len(program.function_modules_used)))
                    self._log(t("log_bapis_detected", count=len(program.bapis_used)))

                    if program.tables_used:
                        tables_preview = ", ".join(sorted(program.tables_used)[:8])
                        if len(program.tables_used) > 8:
                            tables_preview += " ..."
                        self._log(f"  Tables: {tables_preview}", "info")

                    if program.function_modules_used:
                        fm_preview = ", ".join(sorted(program.function_modules_used)[:5])
                        if len(program.function_modules_used) > 5:
                            fm_preview += " ..."
                        self._log(f"  FMs: {fm_preview}", "info")

                    if program.has_exec_sql:
                        self._log(t("log_exec_sql"), "info")

                    # 2. Transform
                    self._log(t("log_transforming"), "info")
                    result = transformer.transform(program, source_file=filepath)

                    self._log(t("log_changes_auto", count=result.auto_converted), "success")
                    self._log(t("log_changes_review", count=result.needs_review), "warning")
                    self._log(t("log_changes_manual", count=result.manual_only), "error")

                    total_auto += result.auto_converted
                    total_review += result.needs_review
                    total_manual += result.manual_only

                    # 3. Generate converted ABAP
                    self._log(t("log_generating"), "info")
                    rel_dir = os.path.relpath(os.path.dirname(filepath), input_dir)
                    if rel_dir == ".":
                        file_output_dir = output_dir
                    else:
                        file_output_dir = os.path.join(output_dir, rel_dir)

                    base, ext = os.path.splitext(filename)
                    output_path = os.path.join(file_output_dir, f"{base}_s4{ext}")
                    os.makedirs(file_output_dir, exist_ok=True)
                    generator.generate(result, output_path)

                    # 4. Backup original if enabled
                    if options.backup_originals:
                        backup_dir = os.path.join(output_dir, "_backup")
                        backup_path = BackupManager.backup_file(filepath, backup_dir)
                        self._log(t("log_backup_created", path=os.path.basename(backup_path)), "info")

                    all_results.append((filepath, result))
                    self._log(t("log_file_complete", file=display_name), "success")
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    self._log(f"  ERROR: {str(e)}", "error")
                    self._log(f"  {traceback.format_exc()}", "error")

            # 5. Generate batch report
            if report_gen and all_results and not self.cancel_flag:
                self._log(f"\n{t('log_generating_report')}", "header")
                report_results = [result for _, result in all_results]
                report_dir = os.path.join(output_dir, "_reports")
                report_gen.generate(report_results, report_dir)
                self._log(t("log_report_saved", path=report_dir), "success")

            # Summary
            self._log(f"\n{'=' * 60}", "header")
            self._log(t("log_migration_complete"), "header")
            self._log(f"{'=' * 60}", "header")
            self._log(t("log_success", count=success_count), "success")
            if error_count > 0:
                self._log(t("log_errors", count=error_count), "error")
            self._log(t("log_summary_auto", count=total_auto), "success")
            self._log(t("log_summary_review", count=total_review), "warning")
            self._log(t("log_summary_manual", count=total_manual), "error")
            self._log(t("log_output", path=output_dir), "info")

        except Exception as e:
            self._log(f"Fatal error: {str(e)}", "error")
            self._log(traceback.format_exc(), "error")

        finally:
            self._finish()

    def _finish(self):
        self.is_running = False
        self.root.after(0, lambda: self.run_button.configure(state=tk.NORMAL))
        self.root.after(0, lambda: self.cancel_button.configure(state=tk.DISABLED))
        self.root.after(0, lambda: self.status_var.set(self._t("status_complete")))
        self.root.after(0, lambda: self.progress_var.set(100))


def run_cli(args):
    """Execute conversion without GUI."""
    print("=" * 60)
    print("SAP ECC to S/4HANA Migration - Starting (CLI Mode)")
    print("=" * 60)

    input_dir = args.input.strip()
    output_dir = args.output.strip()

    if not os.path.isdir(input_dir):
        print(f"[ERROR] Input directory does not exist: {input_dir}")
        sys.exit(1)

    print(f"Input:          {input_dir}")
    print(f"Output:         {output_dir}")
    print(f"Source Version: {args.source_version}")
    print(f"Target Version: {args.target_version}")
    print(f"Module Filter:  {args.module}")
    print(f"Encoding:       {args.encoding}")

    # Parse module filter
    if args.module == "ALL":
        sap_modules = ["ALL"]
    elif args.module == "FI/CO":
        sap_modules = ["FI", "CO"]
    elif args.module == "ABAP Language":
        sap_modules = ["ABAP"]
    else:
        sap_modules = [args.module]

    extensions = [e.strip() for e in args.ext.split(",")]
    abap_files = []
    for root_dir, dirs, files in os.walk(input_dir):
        for f in files:
            if any(f.endswith(ext) for ext in extensions):
                abap_files.append(os.path.join(root_dir, f))

    if not abap_files:
        print(f"[WARNING] No ABAP files found with extensions: {extensions}")
        sys.exit(0)

    print(f"Found {len(abap_files)} ABAP file(s).")

    options = MigrationOptions(
        source_version=args.source_version,
        target_version=args.target_version,
        sap_modules=sap_modules,
        encoding=args.encoding,
        extensions=extensions,
        modernize_syntax=not args.no_modernize,
        convert_tables=not args.no_tables,
        convert_bapis=not args.no_bapis,
        convert_fm=not args.no_fm,
        generate_report=not args.no_report,
        add_comments=not args.no_comments,
        backup_originals=not args.no_backup,
        report_format=args.report_format,
    )

    parser = AbapParser(encoding=args.encoding)
    transformer = S4Transformer(options)
    generator = AbapCodeGenerator(options)
    report_gen = ReportGenerator(options) if options.generate_report else None

    success_count = 0
    error_count = 0
    total_auto = 0
    total_review = 0
    total_manual = 0
    all_results = []

    for filepath in abap_files:
        filename = os.path.basename(filepath)
        print(f"\n--- Processing: {filename} ---")
        try:
            program = parser.parse_file(filepath)
            print(f"  Report: {program.report_name or '(unknown)'}")
            print(f"  Lines: {program.total_lines}")
            print(f"  Tables: {len(program.tables_used)}, FMs: {len(program.function_modules_used)}, BAPIs: {len(program.bapis_used)}")

            result = transformer.transform(program, source_file=filepath)
            print(f"  Changes - Auto: {result.auto_converted}, Review: {result.needs_review}, Manual: {result.manual_only}")

            total_auto += result.auto_converted
            total_review += result.needs_review
            total_manual += result.manual_only

            # Generate converted file
            rel_dir = os.path.relpath(os.path.dirname(filepath), input_dir)
            if rel_dir == ".":
                file_output_dir = output_dir
            else:
                file_output_dir = os.path.join(output_dir, rel_dir)

            base, ext = os.path.splitext(filename)
            output_path = os.path.join(file_output_dir, f"{base}_s4{ext}")
            os.makedirs(file_output_dir, exist_ok=True)
            generator.generate(result, output_path)

            # Backup
            if options.backup_originals:
                backup_dir = os.path.join(output_dir, "_backup")
                BackupManager.backup_file(filepath, backup_dir)

            all_results.append((filepath, result))
            success_count += 1
            print("  Success.")

        except Exception as e:
            error_count += 1
            print(f"  [ERROR] {str(e)}")
            traceback.print_exc()

    # Generate report
    if report_gen and all_results:
        print("\nGenerating impact analysis report...")
        report_results = [result for _, result in all_results]
        report_dir = os.path.join(output_dir, "_reports")
        report_gen.generate(report_results, report_dir)
        print(f"Report saved to: {report_dir}")

    print(f"\n{'=' * 60}")
    print("Migration Complete")
    print(f"{'=' * 60}")
    print(f"  Success: {success_count} file(s)")
    if error_count > 0:
        print(f"  Errors:  {error_count} file(s)")
    print(f"  Auto-converted: {total_auto}")
    print(f"  Needs review:   {total_review}")
    print(f"  Manual only:    {total_manual}")

    if error_count > 0:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="SAP ECC to S/4HANA Migration Tool")
    parser.add_argument("-i", "--input", help="Input folder containing ABAP files (CLI execution)")
    parser.add_argument("-o", "--output", help="Output folder for converted ABAP files")
    parser.add_argument("-e", "--encoding", default="utf-8",
                        help="Source encoding (default: utf-8)")
    parser.add_argument("--ext", default=".abap,.txt,.prog,.ABAP",
                        help="Comma-separated file extensions to process (default: .abap,.txt,.prog,.ABAP)")
    parser.add_argument("--source-version", default="ECC 6.08",
                        choices=["ECC 6.0", "ECC 6.04", "ECC 6.05", "ECC 6.06", "ECC 6.07", "ECC 6.08"],
                        help="Source SAP version (default: ECC 6.08)")
    parser.add_argument("--target-version", default="S/4HANA 2023",
                        choices=["S/4HANA 1709", "S/4HANA 1809", "S/4HANA 1909",
                                 "S/4HANA 2020", "S/4HANA 2021", "S/4HANA 2022", "S/4HANA 2023"],
                        help="Target S/4HANA version (default: S/4HANA 2023)")
    parser.add_argument("--module", default="ALL",
                        choices=["ALL", "FI/CO", "MM", "SD", "BP", "PP", "ABAP Language"],
                        help="SAP module filter (default: ALL)")
    parser.add_argument("--report-format", default="Both",
                        choices=["HTML", "CSV", "Both"],
                        help="Report output format (default: Both)")

    parser.add_argument("--no-modernize", action="store_true",
                        help="Disable syntax modernization")
    parser.add_argument("--no-tables", action="store_true",
                        help="Disable table conversion")
    parser.add_argument("--no-bapis", action="store_true",
                        help="Disable BAPI conversion")
    parser.add_argument("--no-fm", action="store_true",
                        help="Disable function module conversion")
    parser.add_argument("--no-report", action="store_true",
                        help="Disable report generation")
    parser.add_argument("--no-comments", action="store_true",
                        help="Disable adding migration comments")
    parser.add_argument("--no-backup", action="store_true",
                        help="Disable backup of original files")

    args = parser.parse_args()

    # If standard inputs are provided, run CLI, else GUI
    if args.input and args.output:
        run_cli(args)
    elif args.input or args.output:
        print("[ERROR] Both -i/--input and -o/--output must be provided for CLI execution.")
        sys.exit(1)
    else:
        root = tk.Tk()

        icon_path = os.path.join(BASE_DIR, "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)

        app = AbapToS4App(root)
        root.mainloop()


if __name__ == "__main__":
    main()
