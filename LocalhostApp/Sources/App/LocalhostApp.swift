import SwiftUI
import ApplicationServices

@main
struct LocalhostApp: App {
    @StateObject private var appState = AppState()
    
    init() {
        requestAccessibilityPermission()
        HotkeyManager.shared.register()
    }
    
    func requestAccessibilityPermission() {
        let options: NSDictionary = [kAXTrustedCheckOptionPrompt.takeRetainedValue() as String: true]
        let accessEnabled = AXIsProcessTrustedWithOptions(options)
        
        if !accessEnabled {
            print("Please grant Accessibility permission in System Preferences")
        }
    }
    
    var body: some Scene {
        MenuBarExtra("Localhost", systemImage: "cpu") {
            Button("Show (Cmd+Shift+.)") {
                HotkeyManager.shared.show()
            }
            Divider()
            Button("Quit") {
                NSApplication.shared.terminate(nil)
            }
        }
    }
}

class AppState: ObservableObject {
    init() {
        // Start the background bridge connection
        BridgeService.shared.start()
        
        // Set up cleanup on app termination
        NotificationCenter.default.addObserver(
            forName: NSApplication.willTerminateNotification,
            object: nil,
            queue: .main
        ) { _ in
            BridgeService.shared.stop()
        }
    }
    
    deinit {
        NotificationCenter.default.removeObserver(self)
    }
}
