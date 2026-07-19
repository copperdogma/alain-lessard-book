import Foundation
import ImageIO
import Vision

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write(Data("usage: decode_qr_vision.swift <image>\n".utf8))
    exit(2)
}

let imageURL = URL(fileURLWithPath: CommandLine.arguments[1])
guard
    let source = CGImageSourceCreateWithURL(imageURL as CFURL, nil),
    let image = CGImageSourceCreateImageAtIndex(source, 0, nil)
else {
    FileHandle.standardError.write(Data("could not read image: \(imageURL.path)\n".utf8))
    exit(3)
}

let request = VNDetectBarcodesRequest()
request.symbologies = [.qr]
let handler = VNImageRequestHandler(cgImage: image, options: [:])

do {
    try handler.perform([request])
} catch {
    FileHandle.standardError.write(Data("Vision barcode detection failed: \(error)\n".utf8))
    exit(4)
}

let payloads = (request.results ?? []).compactMap { $0.payloadStringValue }
guard !payloads.isEmpty else {
    FileHandle.standardError.write(Data("no QR code decoded\n".utf8))
    exit(5)
}

for payload in payloads {
    print(payload)
}
