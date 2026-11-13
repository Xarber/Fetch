// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "FetchCore", platforms: [.macOS(.v14), .iOS(.v17)], products: [.library(name: "FetchCore", targets: ["FetchCore"])], targets: [.target(name: "FetchCore", path: "FetchCore"), .testTarget(name: "FetchCoreTests", dependencies: ["FetchCore"], path: "FetchCoreTests")])
