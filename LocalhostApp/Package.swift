// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "LocalhostApp",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(name: "LocalhostApp", targets: ["LocalhostApp"])
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "LocalhostApp",
            dependencies: [],
            path: ".",
            resources: [
                .process("Info.plist")
            ]
        )
    ]
)
