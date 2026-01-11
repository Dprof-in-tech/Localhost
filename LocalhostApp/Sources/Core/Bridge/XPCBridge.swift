import AppKit

struct BridgeMessage: Codable {
    let type: String
    let payload: Dict
}

struct BridgeResponse: Codable {
    let status: String
    let response: String?
    let message: String?
}

// Helper for loose JSON payloads
struct Dict: Codable {
    var value: [String: String]
    
    init(_ value: [String: String]) {
        self.value = value
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        for (key, val) in value {
            let codingKey = CodingKeys(stringValue: key)!
            try container.encode(val, forKey: codingKey)
        }
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        var val = [String: String]()
        for key in container.allKeys {
            val[key.stringValue] = try container.decode(String.self, forKey: key)
        }
        self.value = val
    }
    
    struct CodingKeys: CodingKey {
        var stringValue: String
        var intValue: Int?
        
        init?(stringValue: String) { self.stringValue = stringValue }
        init?(intValue: Int) { return nil }
    }
}

class BridgeService {
    static let shared = BridgeService()
    
    private var process: Process?
    private var inputPipe = Pipe()
    private var outputPipe = Pipe()
    private var errorPipe = Pipe()
    
    // Simple callback queue (in real app, use IDs)
    private var callbacks: [((String) -> Void)] = []
    
    // Buffer for incomplete JSON lines
    private var outputBuffer = ""
    
    func start() {
        guard process == nil else { return }
        
        process = Process()
        
        // Path Resolution Strategy:
        // 1. Distribution Path (~/.localhost)
        // 2. Development Path (Hardcoded Fallback)
        
        let fileManager = FileManager.default
        let home = fileManager.homeDirectoryForCurrentUser.path
        
        let distPython = "\(home)/.localhost/venv/bin/python"
        let distScript = "\(home)/.localhost/python_brain/main.py"
        
        let devPython = "/Users/prof/Documents/PROJECTS/Localhost/python_brain/venv/bin/python"
        let devScript = "/Users/prof/Documents/PROJECTS/Localhost/python_brain/main.py"
        
        var finalPython = ""
        var finalScript = ""
        
        if fileManager.fileExists(atPath: distScript) {
            print("Bridge: Using Distributed Backend at ~/.localhost")
            finalPython = distPython
            finalScript = distScript
        } else {
            print("Bridge: ~/.localhost not found. Falling back to Dev Path.")
            finalPython = devPython
            finalScript = devScript
        }
        
        process?.executableURL = URL(fileURLWithPath: finalPython)
        process?.arguments = ["-u", finalScript] // -u for unbuffered binary stdout
        
        process?.standardInput = inputPipe
        process?.standardOutput = outputPipe
        process?.standardError = errorPipe
        
        process?.environment = [
            "PYTHONPATH": (finalScript as NSString).deletingLastPathComponent,
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin"
        ]
        
        // Set up termination handler to clean up properly
        process?.terminationHandler = { [weak self] process in
            print("Python process terminated with status: \(process.terminationStatus)")
            self?.process = nil
        }
        
        outputPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard !data.isEmpty, let self = self else { return }
            
            if let str = String(data: data, encoding: .utf8) {
                // Add to buffer
                self.outputBuffer += str
                
                // Process complete lines (ending with newline)
                while let newlineRange = self.outputBuffer.range(of: "\n") {
                    let line = String(self.outputBuffer[..<newlineRange.lowerBound])
                    self.outputBuffer.removeSubrange(..<newlineRange.upperBound)
                    
                    if !line.trimmingCharacters(in: .whitespaces).isEmpty {
                        self.handleResponse(line)
                    }
                }
            }
        }
        
        errorPipe.fileHandleForReading.readabilityHandler = { handle in
             let data = handle.availableData
             if let str = String(data: data, encoding: .utf8), !str.isEmpty {
                 print("PYTHON LOG: \(str)")
             }
        }
        
        do {
            try process?.run()
            print("Python process started (PID: \(process?.processIdentifier ?? -1))")
        } catch {
            print("Failed to start python process: \(error)")
        }
    }
    
    func stop() {
        guard let process = process, process.isRunning else { return }
        
        // Send graceful termination signal
        process.terminate()
        
        // Wait briefly for graceful shutdown
        DispatchQueue.global().asyncAfter(deadline: .now() + 1.0) { [weak self] in
            if let process = self?.process, process.isRunning {
                // Force kill if still running
                process.interrupt()
            }
        }
    }
    
    deinit {
        stop()
    }
    
    func query(_ text: String, completion: @escaping (String) -> Void) {
        guard process?.isRunning == true else {
            print("ERROR: Python process is not running!")
            completion("Error: Python backend not running")
            return
        }
        
        let message = BridgeMessage(
            type: "query",
            payload: Dict(["text": text])
        )
        
        print("SWIFT → PYTHON: Sending query: \(text)")
        send(message)
        // Store callback (simple LIFO/FIFO for now, robust version needs IDs)
        callbacks.append(completion)
    }
    
    func getContext(completion: @escaping (String) -> Void) {
        guard process?.isRunning == true else {
            completion("None")
            return
        }
        
        let message = BridgeMessage(
            type: "get_context",
            payload: Dict([:])
        )
        
        print("SWIFT → PYTHON: Requesting context")
        send(message)
        callbacks.append(completion)
    }
    
    private func send(_ message: BridgeMessage) {
        guard let data = try? JSONEncoder().encode(message) else {
            print("ERROR: Failed to encode message")
            return
        }
        
        if let jsonString = String(data: data, encoding: .utf8) {
            print("SWIFT → PYTHON (JSON): \(jsonString)")
        }
        
        do {
            try inputPipe.fileHandleForWriting.write(contentsOf: data)
            try inputPipe.fileHandleForWriting.write(contentsOf: "\n".data(using: .utf8)!)
        } catch {
            print("ERROR: Failed to write to pipe: \(error)")
        }
    }
    
    private func handleResponse(_ jsonString: String) {
        print("PYTHON → SWIFT (raw): \(jsonString)")
        
        guard let data = jsonString.data(using: .utf8) else {
            print("ERROR: Failed to convert response to data")
            return
        }
        
        do {
            let result = try JSONDecoder().decode(BridgeResponse.self, from: data)
            let responseText = result.response ?? result.message ?? "Unknown error"
            
            print("PYTHON → SWIFT (decoded): \(responseText)")
            
            if result.status == "shutdown" {
                print("Bridge: Received shutdown signal. Terminating App.")
                NSApplication.shared.terminate(nil)
                return
            }
            
            DispatchQueue.main.async {
                if !self.callbacks.isEmpty {
                    let callback = self.callbacks.removeFirst()
                    callback(responseText)
                } else {
                    print("WARNING: Received response but no callback waiting!")
                }
            }
        } catch {
            print("ERROR: Failed to decode bridge response: \(error)")
            print("ERROR: Raw JSON was: \(jsonString)")
            
            // If we can't decode, still call the callback with the raw response
            DispatchQueue.main.async {
                if !self.callbacks.isEmpty {
                    let callback = self.callbacks.removeFirst()
                    callback("Error decoding response: \(jsonString)")
                }
            }
        }
    }
}
