import Carbon
import SwiftUI

class HotkeyManager {
    static let shared = HotkeyManager()
    private var window: FloatingWindow?
    
    func register() {
        var eventHandler: EventHandlerRef?
        var eventType = EventTypeSpec(
            eventClass: OSType(kEventClassKeyboard),
            eventKind: OSType(kEventHotKeyPressed)
        )
        
        let handler: EventHandlerUPP = { (handlerRef, eventRef, userData) in
            print("Hotkey pressed!")
            DispatchQueue.main.async {
                HotkeyManager.shared.show()
            }
            return noErr
        }
        
        InstallEventHandler(
            GetApplicationEventTarget(),
            handler,
            1, &eventType,
            nil, &eventHandler
        )
        
        var hotKeyRef: EventHotKeyRef?
        // Register Cmd+Shift+.
        // period is kVK_ANSI_Period (0x2F = 47)
        RegisterEventHotKey(
            47,
            UInt32(cmdKey | shiftKey),
            EventHotKeyID(signature: FourCharCode(0x4C4F43), id: 1),
            GetApplicationEventTarget(),
            0,
            &hotKeyRef
        )
    }
    
    func show() {
        if window == nil {
            window = FloatingWindow()
        }
        
        // Properly activate the app and show the window
        NSApp.activate(ignoringOtherApps: true)
        window?.makeKeyAndOrderFront(nil)
    }
    
    func hide() {
        window?.orderOut(nil)
    }
}

class FloatingWindow: NSPanel {
    private let hostingView: NSHostingView<FloatingBarView>
    
    init() {
        // Create the hosting view first
        hostingView = NSHostingView(rootView: FloatingBarView())
        
        super.init(
            contentRect: NSRect(x: 0, y: 0, width: 600, height: 80),
            styleMask: [.nonactivatingPanel, .borderless, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        
        self.level = .floating
        self.backgroundColor = .clear
        self.isOpaque = false
        self.hasShadow = true
        self.isMovableByWindowBackground = true
        
        // Allow the window to become key so it can receive keyboard input
        self.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        
        // Prevent automatic window closing behaviors that trigger ViewBridge warnings
        self.hidesOnDeactivate = false
        
        // Fixed width, variable height
        self.minSize = NSSize(width: 600, height: 80)
        self.maxSize = NSSize(width: 600, height: 500)
        
        self.contentView = hostingView
        
        // Enable autoresizing based on SwiftUI content
        hostingView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            hostingView.leadingAnchor.constraint(equalTo: contentView!.leadingAnchor),
            hostingView.trailingAnchor.constraint(equalTo: contentView!.trailingAnchor),
            hostingView.topAnchor.constraint(equalTo: contentView!.topAnchor),
            hostingView.bottomAnchor.constraint(equalTo: contentView!.bottomAnchor)
        ])
        
        self.center()
    }
    
    // Override to allow the panel to become key window for keyboard input
    override var canBecomeKey: Bool {
        return true
    }
    
    // Override to allow the panel to become main window
    override var canBecomeMain: Bool {
        return true
    }
}
