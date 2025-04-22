from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
import yaml
import subprocess
import json
import os


class GhostscaleGUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=dp(10), spacing=dp(10), **kwargs)

        self.header = Label(text="Ghostscale VPN Wrapper Manager", font_size='20sp', size_hint_y=None, height=dp(40))
        self.add_widget(self.header)

        self.status_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        self.status_icon = Image(size_hint_x=None, width=dp(30))
        self.status_text = Label(text="Loading status...", halign='left')
        self.status_box.add_widget(self.status_icon)
        self.status_box.add_widget(self.status_text)
        self.add_widget(self.status_box)

        self.exit_button = Button(text="Change Exit Node", size_hint_y=None, height=dp(40))
        self.exit_button.bind(on_press=self.show_exit_node_popup)
        self.add_widget(self.exit_button)

        self.program_list = ScrollView(size_hint=(1, 1))
        self.program_grid = GridLayout(cols=1, spacing=dp(10), size_hint_y=None, padding=(dp(5), dp(5)))
        self.program_grid.bind(minimum_height=self.program_grid.setter('height'))
        self.program_list.add_widget(self.program_grid)
        self.add_widget(self.program_list)

        self.refresh_button = Button(text="Refresh Programs", size_hint_y=None, height=dp(40))
        self.refresh_button.bind(on_press=self.load_programs)
        self.add_widget(self.refresh_button)

        self.status_label = Label(text="", size_hint_y=None, height=dp(30))
        self.add_widget(self.status_label)

        self.update_status()
        self.load_programs()

    def run_cli(self, command):
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr)
            return result.stdout
        except Exception as e:
            return f"Error: {e}"

    def update_status(self):
        output = self.run_cli(["ghostscale", "status"])
        try:
            active_node = output.strip().replace("Active Exit Node: ", "")
            color = "red.png" if not active_node or active_node == "-" else "green.png"
            icon_path = os.path.join(os.path.dirname(__file__), color)
            self.status_icon.source = icon_path
            if active_node and active_node != "-":
                self.status_text.text = f"Active Exit Node: {active_node}"
            else:
                self.status_text.text = "No active Exit Node"
        except Exception as e:
            self.status_text.text = f"Status error: {e}"

    def show_exit_node_popup(self, instance):
        raw = self.run_cli(["ghostscale", "exits"])
        try:
            data = yaml.safe_load(raw)
            exit_list = data.get("exit_nodes", [])
            exit_nodes = ["- disable -"] + [node["ip"] for node in exit_list if isinstance(node, dict) and node.get("online")]
        except Exception as e:
            self.status_label.text = f"Error loading exits: {e}"
            return

        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        spinner = Spinner(text="Choose Exit Node", values=exit_nodes)
        layout.add_widget(spinner)

        btn_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        ok_btn = Button(text="Apply")
        cancel_btn = Button(text="Cancel")
        btn_box.add_widget(ok_btn)
        btn_box.add_widget(cancel_btn)
        layout.add_widget(btn_box)

        popup = Popup(title="Select Exit Node", content=layout, size_hint=(0.8, 0.5))

        def apply_exit(*args):
            choice = spinner.text
            if choice == "- disable -":
                self.run_cli(["ghostscale", "disable-exit"])
            else:
                self.run_cli(["ghostscale", "set-exit", choice])
            popup.dismiss()
            self.update_status()

        ok_btn.bind(on_press=apply_exit)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def load_programs(self, *args):
        self.program_grid.clear_widgets()
        output = self.run_cli(["ghostscale", "list"])
        try:
            config = yaml.safe_load(output)
        except yaml.YAMLError as e:
            self.status_label.text = f"YAML parse error: {e}"
            return

        if not isinstance(config, dict):
            self.status_label.text = "Invalid config format"
            return

        for prog, data in config.items():
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10), padding=(dp(5), 0))
            label = Label(text=f"{prog} ({data['status']})", size_hint_x=0.6)
            toggle = ToggleButton(text="Enable" if data['status'] == 'disabled' else "Disable", size_hint_x=0.4)
            toggle.state = 'normal' if data['status'] == 'disabled' else 'down'
            toggle.bind(on_press=lambda btn, p=prog: self.toggle_program(p))
            row.add_widget(label)
            row.add_widget(toggle)
            self.program_grid.add_widget(row)

    def toggle_program(self, program):
        result = self.run_cli(["ghostscale", "toggle", program])
        self.status_label.text = result.strip()
        self.update_status()
        self.load_programs()


class GhostscaleApp(App):
    def build(self):
        return GhostscaleGUI()


def main():
    GhostscaleApp().run()


if __name__ == "__main__":
    main()