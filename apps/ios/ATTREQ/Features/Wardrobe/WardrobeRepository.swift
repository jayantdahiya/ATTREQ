//
//  WardrobeRepository.swift
//  ATTREQ
//
//  Wardrobe API calls (M2). Backend contract:
//  apps/api/src/attreq_api/api/v1/endpoints/wardrobe.py
//  - GET  /wardrobe/items?page=&page_size=   (page >= 1, page_size 1...100, default 50)
//  - GET  /wardrobe/items/{item_id}
//  - POST /wardrobe/upload                    multipart field name "file",
//    JPG/PNG only (extension + image/* content type validated server-side).
//

import Foundation

/// Stateless facade over the wardrobe endpoints. Mirrors RN
/// `apps/mobile/src/lib/api/wardrobe.ts`.
final class WardrobeRepository: Sendable {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    /// `GET /wardrobe/items` — the user's wardrobe, newest first, paginated.
    func list(page: Int = 1, pageSize: Int = 50) async throws -> WardrobeListResponse {
        try await apiClient.request(
            Endpoint(
                method: .get,
                path: "wardrobe/items",
                query: [
                    URLQueryItem(name: "page", value: String(page)),
                    URLQueryItem(name: "page_size", value: String(pageSize)),
                ]
            )
        )
    }

    /// `GET /wardrobe/items/{id}` — a single item (used to poll processing status).
    func item(id: String) async throws -> WardrobeItem {
        try await apiClient.request(
            Endpoint(method: .get, path: "wardrobe/items/\(id)")
        )
    }

    /// `POST /wardrobe/upload` — multipart upload of one clothing photo.
    /// The backend requires the part name `file` and a `.jpg`/`.jpeg`/`.png`
    /// filename extension.
    func upload(imageData: Data, filename: String = "photo.jpg") async throws -> WardrobeUploadResponse {
        try await apiClient.request(
            Endpoint(
                method: .post,
                path: "wardrobe/upload",
                body: .multipart([
                    MultipartField(
                        name: "file",
                        filename: filename,
                        contentType: Self.mimeType(forFilename: filename),
                        data: imageData
                    ),
                ])
            )
        )
    }

    /// `image/jpeg` unless the filename says PNG (the only two types the
    /// backend accepts).
    private static func mimeType(forFilename filename: String) -> String {
        filename.lowercased().hasSuffix(".png") ? "image/png" : "image/jpeg"
    }
}
