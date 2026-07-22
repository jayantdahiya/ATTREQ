//
//  WardrobeRepository.swift
//  ATTREQ
//
//  Wardrobe API calls (M2, extended RI-7). Backend contract:
//  apps/api/src/attreq_api/api/v1/endpoints/wardrobe.py
//  - GET    /wardrobe/items?status=&page=&page_size=   (status defaults "active";
//    page >= 1, page_size 1...100, default 50)
//  - GET    /wardrobe/items/{item_id}                  (includes `photos`)
//  - PUT    /wardrobe/items/{item_id}                  manual tag/price/brand edits
//  - PATCH  /wardrobe/items/{item_id}/status           archive/unarchive
//  - POST   /wardrobe/upload                    multipart field name "file",
//    JPG/PNG only (extension + image/* content type validated server-side).
//  - POST   /wardrobe/items/{item_id}/photos    add an extra photo (multipart "file")
//  - GET    /wardrobe/items/{item_id}/photos    list an item's photos
//  - DELETE /wardrobe/items/{item_id}/photos/{photo_id}
//  - POST   /wardrobe/batch-upload              multiple files, field name "files"
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
    ///
    /// - Parameter status: `"active"` (default) or `"archived"`. The backend
    ///   defaults to `"active"` too when the param is omitted; sent explicitly
    ///   here so the archived-items view can request the other bucket.
    func list(page: Int = 1, pageSize: Int = 50, status: String = "active") async throws -> WardrobeListResponse {
        try await apiClient.request(
            Endpoint(
                method: .get,
                path: "wardrobe/items",
                query: [
                    URLQueryItem(name: "page", value: String(page)),
                    URLQueryItem(name: "page_size", value: String(pageSize)),
                    URLQueryItem(name: "status", value: status),
                ]
            )
        )
    }

    /// `GET /wardrobe/items/{id}` — a single item (used to poll processing
    /// status, and by the item detail screen). Includes `photos`.
    func item(id: String) async throws -> WardrobeItem {
        try await apiClient.request(
            Endpoint(method: .get, path: "wardrobe/items/\(id)")
        )
    }

    /// `PUT /wardrobe/items/{id}` — manual tag/price/brand edits. Returns the
    /// updated item (without `photos` — same response shape as the list entry
    /// on this path; re-fetch via `item(id:)` if the gallery needs refreshing).
    func update(itemId: String, body: WardrobeItemUpdateRequest) async throws -> WardrobeItem {
        try await apiClient.request(
            Endpoint(method: .put, path: "wardrobe/items/\(itemId)", body: .json(body))
        )
    }

    /// `PATCH /wardrobe/items/{id}/status` — archive or unarchive. Returns the
    /// full item (with `photos`). 404 if not found/owned; 422 if `status`
    /// isn't `"active"`/`"archived"`.
    func setStatus(itemId: String, status: WardrobeItemStatus) async throws -> WardrobeItem {
        try await apiClient.request(
            Endpoint(
                method: .patch,
                path: "wardrobe/items/\(itemId)/status",
                body: .json(WardrobeItemStatusUpdateRequest(status: status.rawValue))
            )
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

    /// `POST /wardrobe/batch-upload` — multiple images in one request, up to
    /// the server-enforced cap (raised to 20 in RI-7; each part uses the
    /// repeated field name `files`, matching the backend's `files:
    /// list[UploadFile]` parameter). One bad image never fails the rest of
    /// the batch server-side.
    func batchUpload(imagesData: [Data]) async throws -> [WardrobeUploadResponse] {
        try await apiClient.request(
            Endpoint(
                method: .post,
                path: "wardrobe/batch-upload",
                body: .multipart(
                    imagesData.enumerated().map { index, data in
                        let filename = "photo-\(index).jpg"
                        return MultipartField(
                            name: "files",
                            filename: filename,
                            contentType: Self.mimeType(forFilename: filename),
                            data: data
                        )
                    }
                )
            )
        )
    }

    /// `POST /wardrobe/items/{id}/photos` — add an extra photo to an existing
    /// item. Background-processes bg-removal + thumbnail only (no
    /// re-classification). Poll `photos(itemId:)` for the result.
    func addPhoto(
        itemId: String,
        imageData: Data,
        filename: String = "photo.jpg"
    ) async throws -> WardrobeItemPhotoUploadResponse {
        try await apiClient.request(
            Endpoint(
                method: .post,
                path: "wardrobe/items/\(itemId)/photos",
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

    /// `GET /wardrobe/items/{id}/photos` — every photo attached to the item.
    func photos(itemId: String) async throws -> [WardrobeItemPhoto] {
        try await apiClient.request(
            Endpoint(method: .get, path: "wardrobe/items/\(itemId)/photos")
        )
    }

    /// `DELETE /wardrobe/items/{id}/photos/{photoId}`. 400 if it's the
    /// primary photo (no "make primary" UI exists to work around that yet —
    /// this milestone doesn't build one).
    func deletePhoto(itemId: String, photoId: String) async throws {
        try await apiClient.requestVoid(
            Endpoint(method: .delete, path: "wardrobe/items/\(itemId)/photos/\(photoId)")
        )
    }

    /// `image/jpeg` unless the filename says PNG (the only two types the
    /// backend accepts).
    private static func mimeType(forFilename filename: String) -> String {
        filename.lowercased().hasSuffix(".png") ? "image/png" : "image/jpeg"
    }
}
