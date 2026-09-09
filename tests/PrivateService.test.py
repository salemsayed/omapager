#!/usr/bin/env python3
"""Verify plugin-local service sharing across real QML component lifecycles."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
QS = shutil.which("qs")

@unittest.skipUnless(QS, "Quickshell required")
class PrivateServiceTests(unittest.TestCase):
    def test_late_subscribers_reload_replacement_and_teardown(self):
        with tempfile.TemporaryDirectory(prefix="plugin-private-service-test-") as temporary:
            base = Path(temporary)
            runtime = base / "runtime"; runtime.mkdir(mode=0o700)
            shutil.copy2(ROOT / "PrivateService.js", base / "PrivateService.js")
            (base / "Publisher.qml").write_text('''import QtQuick
import "PrivateService.js" as PrivateService
Item { id: publisher; property int value: 7
 Component.onCompleted: PrivateService.publish(publisher)
 Component.onDestruction: PrivateService.release(publisher)
}''')
            (base / "Subscriber.qml").write_text('''import QtQuick
import "PrivateService.js" as PrivateService
Item { id: subscriber; property var sharedService: null
 Component.onCompleted: PrivateService.subscribe(subscriber)
 Component.onDestruction: PrivateService.unsubscribe(subscriber)
}''')
            (base / "shell.qml").write_text('''import QtQuick
import Quickshell
ShellRoot {
 property int stage: 0
 Loader { id: first; source: "Publisher.qml" }
 Loader { id: subscriber; source: "Subscriber.qml" }
 Loader { id: second; active: false; source: "Publisher.qml" }
 Timer { interval: 100; repeat: true; running: true
   onTriggered: {
     if (stage === 0) {
       if (!subscriber.item.sharedService || subscriber.item.sharedService !== first.item) { Qt.exit(1); return }
       second.active = true
     } else if (stage === 1) {
       if (subscriber.item.sharedService !== second.item) { Qt.exit(2); return }
       first.active = false
     } else if (stage === 2) {
       if (subscriber.item.sharedService !== second.item) { Qt.exit(3); return }
       subscriber.active = false
       second.item.value = 23
       subscriber.active = true
     } else if (stage === 3) {
       if (subscriber.item.sharedService.value !== 23) { Qt.exit(4); return }
       second.active = false
     } else {
       if (subscriber.item.sharedService !== null) { Qt.exit(5); return }
       console.log("PRIVATE_SERVICE_PASS")
       Qt.quit()
     }
     stage++
   }
 }
}''')
            env = dict(os.environ, QT_QPA_PLATFORM="offscreen", XDG_RUNTIME_DIR=str(runtime))
            result = subprocess.run([QS, "-p", str(base)], env=env, capture_output=True, text=True, timeout=5)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn("PRIVATE_SERVICE_PASS", output)
            for error in ("ReferenceError", "TypeError", "Failed to load configuration"):
                self.assertNotIn(error, output)

if __name__ == "__main__": unittest.main(verbosity=2)
