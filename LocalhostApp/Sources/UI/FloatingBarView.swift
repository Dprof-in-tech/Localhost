import SwiftUI

struct FloatingBarView: View {
    @State private var input: String = ""
    @State private var response: String = ""
    @State private var isReasoning: Bool = false
    @State private var loadingText: String = ""
    @State private var loadingIndex: Int = 0
    @State private var contextInfo: String = "None"
    @FocusState private var isFocused: Bool
    
    private let loadingPhrases = [
        "thinking",
        "analyzing",
        "processing",
        "tinkering",
        "spoofing",
        "pondering",
        "computing",
        "reasoning",
        "calculating",
        "synthesizing"
    ]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Top Bar with Context and Close Button
            HStack {
                Text("Context: \(contextInfo)")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.blue.opacity(0.1))
                    .foregroundColor(.blue)
                    .cornerRadius(4)
                
                Spacer()
                
                // Close Button
                Button(action: closeWindow) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 20))
                        .foregroundStyle(.secondary, .quaternary)
                        .symbolRenderingMode(.hierarchical)
                }
                .buttonStyle(.plain)
                .help("Close (Esc)")
            }
            .padding(.horizontal)
            .padding(.top, 10)
            
            // Input Area
            HStack(spacing: 12) {
                Image(systemName: "cpu.fill")
                    .foregroundColor(isReasoning ? .purple : .secondary)
                    .symbolEffect(.pulse, isActive: isReasoning)
                
                if isReasoning {
                    // Show loading text with typewriter effect
                    Text(loadingText)
                        .font(.system(size: 16))
                        .foregroundColor(.secondary)
                        .italic()
                        .transition(.opacity)
                } else {
                    TextField("Ask Localhost...", text: $input)
                        .textFieldStyle(.plain)
                        .font(.system(size: 16))
                        .focused($isFocused)
                        .disabled(isReasoning)
                        .onSubmit {
                            submit()
                        }
                }
                
                if !input.isEmpty && !isReasoning {
                    Button(action: submit) {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.title2)
                    }
                    .buttonStyle(.borderless)
                }
            }
            .padding()
            
            // Response Area (Ghost Drawer)
            if !response.isEmpty {
                Divider()
                    .padding(.horizontal)
                
                ScrollView {
                    Text(response)
                        .font(.system(size: 13))
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .textSelection(.enabled)
                }
                .frame(minHeight: 100, maxHeight: 300)
                .background(Color.gray.opacity(0.1))
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .frame(width: 600)
        .background(.ultraThinMaterial)
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color.white.opacity(0.2), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.15), radius: 20)
        .animation(.spring(response: 0.3, dampingFraction: 0.8), value: response.isEmpty)
        .onAppear {
            isFocused = true
            updateContext()
        }
        .onKeyPress(.escape) {
            closeWindow()
            return .handled
        }
        .onChange(of: isReasoning) { _, newValue in
            if newValue {
                startLoadingAnimation()
            } else {
                loadingText = ""
            }
        }
    }
    
    func startLoadingAnimation() {
        // Reset
        loadingIndex = 0
        loadingText = ""
        
        // Start the typewriter effect
        typewriterEffect()
    }
    
    func typewriterEffect() {
        guard isReasoning else { return }
        
        let currentPhrase = loadingPhrases[loadingIndex % loadingPhrases.count]
        let characters = Array(currentPhrase + "...")
        
        // Reset text for new phrase
        loadingText = ""
        
        // Type out each character
        for (index, character) in characters.enumerated() {
            DispatchQueue.main.asyncAfter(deadline: .now() + Double(index) * 0.08) {
                guard self.isReasoning else { return }
                self.loadingText.append(character)
                
                // When phrase is complete, pause then move to next
                if index == characters.count - 1 {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                        guard self.isReasoning else { return }
                        self.loadingIndex += 1
                        self.typewriterEffect()
                    }
                }
            }
        }
    }
    
    func closeWindow() {
        HotkeyManager.shared.hide()
    }
    
    func updateContext() {
        BridgeService.shared.getContext { context in
            DispatchQueue.main.async {
                self.contextInfo = context
            }
        }
    }
    
    func submit() {
        guard !input.isEmpty else { return }
        isReasoning = true
        response = "" // Clear previous response
        
        let query = input
        input = "" // Clear input
        
        print("DEBUG: Submitting query: \(query)")
        
        // Send to Python
        BridgeService.shared.query(query) { result in
            print("DEBUG: Received result: \(result)")
            DispatchQueue.main.async {
                self.isReasoning = false
                self.response = result
                self.updateContext() // Update context after query in case it changed
                print("DEBUG: Response state updated. isEmpty: \(self.response.isEmpty), count: \(self.response.count)")
            }
        }
    }
}
