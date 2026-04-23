#!/usr/bin/env python3
"""
Interactive Pose Tuner for Humanoid Robot
- Slide joints in real time → see robot move in RViz
- Press Save to store current pose with a name
- Prints final GESTURES dict you can paste into gesture_mapper.py
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import json
import os

JOINT_NAMES = [
    "body_to_arm_joint_right",
    "shoulder_yaw_joint_right",
    "shoulder_pitch_joint_right",
    "elbow_joint_right",
    "palm_to_f1_right",
    "palm_to_f2_right",
    "palm_to_f3_right",
    "body_to_arm_joint_left",
    "shoulder_yaw_joint_left",
    "shoulder_pitch_joint_left",
    "elbow_joint_left",
    "palm_to_f1_left",
    "palm_to_f2_left",
    "palm_to_f3_left",
]

JOINT_LIMITS = {
    "body_to_arm_joint_right":   (-1.57, 1.57),
    "shoulder_yaw_joint_right":  (-1.87, 1.57),
    "shoulder_pitch_joint_right":(-1.57, 1.73),
    "elbow_joint_right":         (0.0,   2.2),
    "palm_to_f1_right":          (-1.0,  1.0),
    "palm_to_f2_right":          (-1.0,  1.0),
    "palm_to_f3_right":          (-1.0,  1.0),
    "body_to_arm_joint_left":    (-1.57, 1.57),
    "shoulder_yaw_joint_left":   (-1.87, 1.57),
    "shoulder_pitch_joint_left": (-1.57, 1.57),
    "elbow_joint_left":          (0.0,   2.2),
    "palm_to_f1_left":           (-1.0,  1.0),
    "palm_to_f2_left":           (-1.0,  1.0),
    "palm_to_f3_left":           (-1.0,  1.0),
}

SAVE_PATH = os.path.expanduser(
    "~/ros2_ws/src/humanoid_robot_description/scripts/my_poses.json"
)


class PublisherNode(Node):
    def __init__(self):
        super().__init__("pose_tuner")
        self.pub = self.create_publisher(JointState, "/joint_states", 10)

    def publish(self, angles):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINT_NAMES
        msg.position = angles
        self.pub.publish(msg)


class PoseTunerApp:
    def __init__(self, root, node):
        self.root = root
        self.node = node
        self.saved_poses = {}
        self.sliders = {}
        self.value_labels = {}

        root.title("Robot Pose Tuner")
        root.configure(bg="#1e1e2e")
        root.resizable(True, True)

        # ── Header ──
        hdr = tk.Frame(root, bg="#1e1e2e")
        hdr.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(hdr, text="🤖 Robot Pose Tuner", font=("Helvetica", 16, "bold"),
                 bg="#1e1e2e", fg="#cdd6f4").pack(side="left")
        tk.Label(hdr, text="Move sliders → robot moves in RViz",
                 font=("Helvetica", 10), bg="#1e1e2e", fg="#6c7086").pack(side="left", padx=16)

        # ── Main area: sliders left, poses right ──
        main = tk.Frame(root, bg="#1e1e2e")
        main.pack(fill="both", expand=True, padx=16, pady=8)

        # Sliders panel
        slider_outer = tk.Frame(main, bg="#313244", bd=0, relief="flat")
        slider_outer.pack(side="left", fill="both", expand=True, padx=(0,10))

        tk.Label(slider_outer, text="Joint Controls", font=("Helvetica", 11, "bold"),
                 bg="#313244", fg="#89b4fa").pack(pady=(10,6))

        canvas = tk.Canvas(slider_outer, bg="#313244", highlightthickness=0)
        scrollbar = ttk.Scrollbar(slider_outer, orient="vertical", command=canvas.yview)
        self.slider_frame = tk.Frame(canvas, bg="#313244")

        self.slider_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.slider_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Build sliders
        right_joints = [j for j in JOINT_NAMES if "right" in j]
        left_joints  = [j for j in JOINT_NAMES if "left"  in j]

        self._make_group("── Right Arm ──", right_joints)
        self._make_group("── Left Arm ──",  left_joints)

        # Buttons row
        btn_frame = tk.Frame(slider_outer, bg="#313244")
        btn_frame.pack(fill="x", pady=10, padx=10)

        self._btn(btn_frame, "Zero All",    self.zero_all,   "#45475a", "#cdd6f4").pack(side="left", padx=4)
        self._btn(btn_frame, "Mirror R→L",  self.mirror_r2l, "#45475a", "#cdd6f4").pack(side="left", padx=4)
        self._btn(btn_frame, "Mirror L→R",  self.mirror_l2r, "#45475a", "#cdd6f4").pack(side="left", padx=4)
        self._btn(btn_frame, "💾 Save Pose", self.save_pose,  "#89b4fa", "#1e1e2e").pack(side="right", padx=4)

        # Poses panel
        pose_outer = tk.Frame(main, bg="#313244", bd=0, width=260)
        pose_outer.pack(side="right", fill="y")
        pose_outer.pack_propagate(False)

        tk.Label(pose_outer, text="Saved Poses", font=("Helvetica", 11, "bold"),
                 bg="#313244", fg="#89b4fa").pack(pady=(10,6))

        self.pose_listbox = tk.Listbox(pose_outer, bg="#1e1e2e", fg="#cdd6f4",
                                       selectbackground="#89b4fa", selectforeground="#1e1e2e",
                                       font=("Helvetica", 10), bd=0, height=14)
        self.pose_listbox.pack(fill="both", expand=True, padx=10)

        pb = tk.Frame(pose_outer, bg="#313244")
        pb.pack(fill="x", padx=10, pady=8)
        self._btn(pb, "Load",   self.load_pose,   "#a6e3a1", "#1e1e2e").pack(fill="x", pady=2)
        self._btn(pb, "Delete", self.delete_pose,  "#f38ba8", "#1e1e2e").pack(fill="x", pady=2)
        self._btn(pb, "Export to gesture_mapper.py",
                  self.export_poses, "#fab387", "#1e1e2e").pack(fill="x", pady=2)

        # Values display
        self.values_text = tk.Text(pose_outer, height=6, bg="#1e1e2e", fg="#a6e3a1",
                                   font=("Courier", 9), bd=0, state="disabled")
        self.values_text.pack(fill="x", padx=10, pady=(4,10))

        # Load existing saved poses
        if os.path.exists(SAVE_PATH):
            with open(SAVE_PATH) as f:
                self.saved_poses = json.load(f)
            for name in self.saved_poses:
                self.pose_listbox.insert("end", name)

        # Start publishing loop
        self._publish_loop()

    def _btn(self, parent, text, cmd, bg, fg):
        return tk.Button(parent, text=text, command=cmd,
                         bg=bg, fg=fg, font=("Helvetica", 9, "bold"),
                         relief="flat", padx=10, pady=5, cursor="hand2",
                         activebackground=bg, activeforeground=fg)

    def _make_group(self, title, joints):
        tk.Label(self.slider_frame, text=title, font=("Helvetica", 10, "bold"),
                 bg="#313244", fg="#cba6f7").pack(pady=(12,4), anchor="w", padx=10)

        for jname in joints:
            lo, hi = JOINT_LIMITS[jname]
            row = tk.Frame(self.slider_frame, bg="#313244")
            row.pack(fill="x", padx=10, pady=3)

            short = jname.replace("_right","_R").replace("_left","_L")\
                         .replace("body_to_arm_joint","body")\
                         .replace("shoulder_yaw_joint","yaw")\
                         .replace("shoulder_pitch_joint","pitch")\
                         .replace("elbow_joint","elbow")\
                         .replace("palm_to_f","f")

            tk.Label(row, text=f"{short:<12}", font=("Courier", 9),
                     bg="#313244", fg="#cdd6f4", width=12, anchor="w").pack(side="left")

            val_lbl = tk.Label(row, text=" 0.00", font=("Courier", 9, "bold"),
                               bg="#313244", fg="#a6e3a1", width=6)
            val_lbl.pack(side="right")

            var = tk.DoubleVar(value=0.0)
            slider = ttk.Scale(row, from_=lo, to=hi, variable=var, orient="horizontal",
                               command=lambda v, j=jname, lbl=val_lbl:
                                   self._on_slide(j, float(v), lbl))
            slider.pack(side="left", fill="x", expand=True, padx=6)

            self.sliders[jname] = var
            self.value_labels[jname] = val_lbl

    def _on_slide(self, joint, value, label):
        label.config(text=f"{value:+.2f}")
        self._update_values_display()

    def _get_angles(self):
        return [round(self.sliders[j].get(), 4) for j in JOINT_NAMES]

    def _update_values_display(self):
        angles = self._get_angles()
        r = angles[:7]
        l = angles[7:]
        txt = f"right: {[round(v,2) for v in r]}\nleft:  {[round(v,2) for v in l]}"
        self.values_text.config(state="normal")
        self.values_text.delete("1.0", "end")
        self.values_text.insert("1.0", txt)
        self.values_text.config(state="disabled")

    def _publish_loop(self):
        self.node.publish(self._get_angles())
        self.root.after(50, self._publish_loop)  # 20 Hz

    def zero_all(self):
        for j in JOINT_NAMES:
            self.sliders[j].set(0.0)
            self.value_labels[j].config(text=" 0.00")
        self._update_values_display()

    def mirror_r2l(self):
        for j in JOINT_NAMES:
            if "right" in j:
                left_j = j.replace("right", "left")
                val = self.sliders[j].get()
                lo, hi = JOINT_LIMITS[left_j]
                mirrored = max(lo, min(hi, val))
                self.sliders[left_j].set(mirrored)
                self.value_labels[left_j].config(text=f"{mirrored:+.2f}")
        self._update_values_display()

    def mirror_l2r(self):
        for j in JOINT_NAMES:
            if "left" in j:
                right_j = j.replace("left", "right")
                val = self.sliders[j].get()
                lo, hi = JOINT_LIMITS[right_j]
                mirrored = max(lo, min(hi, val))
                self.sliders[right_j].set(mirrored)
                self.value_labels[right_j].config(text=f"{mirrored:+.2f}")
        self._update_values_display()

    def save_pose(self):
        name = simpledialog.askstring("Save Pose", "Enter pose name:",
                                      parent=self.root)
        if not name:
            return
        name = name.strip()
        angles = self._get_angles()
        self.saved_poses[name] = angles
        if name not in self.pose_listbox.get(0, "end"):
            self.pose_listbox.insert("end", name)
        with open(SAVE_PATH, "w") as f:
            json.dump(self.saved_poses, f, indent=2)
        messagebox.showinfo("Saved", f'Pose "{name}" saved!')

    def load_pose(self):
        sel = self.pose_listbox.curselection()
        if not sel:
            messagebox.showwarning("Select a pose", "Click a pose name first")
            return
        name = self.pose_listbox.get(sel[0])
        angles = self.saved_poses[name]
        for i, j in enumerate(JOINT_NAMES):
            self.sliders[j].set(angles[i])
            self.value_labels[j].config(text=f"{angles[i]:+.2f}")
        self._update_values_display()

    def delete_pose(self):
        sel = self.pose_listbox.curselection()
        if not sel:
            return
        name = self.pose_listbox.get(sel[0])
        del self.saved_poses[name]
        self.pose_listbox.delete(sel[0])
        with open(SAVE_PATH, "w") as f:
            json.dump(self.saved_poses, f, indent=2)

    def export_poses(self):
        if not self.saved_poses:
            messagebox.showwarning("No poses", "Save some poses first!")
            return
        lines = ["GESTURES = {"]
        for name, angles in self.saved_poses.items():
            r = angles[:7]
            l = angles[7:]
            lines.append(f'    "{name}": [')
            lines.append(f"        {r},")
            lines.append(f"        {l},")
            lines.append(f"    ],")
        lines.append("}")
        code = "\n".join(lines)

        # Show in a popup window
        win = tk.Toplevel(self.root)
        win.title("Copy this into gesture_mapper.py")
        win.configure(bg="#1e1e2e")
        tk.Label(win, text="Copy this GESTURES dict into gesture_mapper.py:",
                 bg="#1e1e2e", fg="#cdd6f4", font=("Helvetica", 10)).pack(padx=16, pady=8)
        txt = tk.Text(win, bg="#1e1e2e", fg="#a6e3a1", font=("Courier", 10),
                      width=72, height=30)
        txt.pack(padx=16, pady=4)
        txt.insert("1.0", code)
        self._btn(win, "Close", win.destroy, "#45475a", "#cdd6f4").pack(pady=8)
        print("\n" + code)


def main():
    rclpy.init()
    node = PublisherNode()

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    root = tk.Tk()
    app = PoseTunerApp(root, node)

    def on_close():
        try:
            node.destroy_node()
            rclpy.shutdown()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.geometry("900x680")
    root.mainloop()


if __name__ == "__main__":
    main()
