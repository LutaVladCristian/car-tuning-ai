from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from firebase_admin import firestore

from app.core.security import _get_app
from app.domain import OperationType, PhotoRecord, PhotoStatus, UserRecord


def _utcnow() -> datetime:
    return datetime.now(UTC)


class PhotoNotFoundError(Exception):
    pass


class PhotoConflictError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class AbstractPhotoStore(ABC):
    @abstractmethod
    def sync_user(self, firebase_uid: str, email: str, display_name: str | None) -> UserRecord:
        raise NotImplementedError

    @abstractmethod
    def get_or_create_user(self, firebase_uid: str, email: str, display_name: str | None) -> UserRecord:
        raise NotImplementedError

    @abstractmethod
    def list_completed_photos(self, firebase_uid: str, skip: int, limit: int) -> tuple[list[PhotoRecord], int]:
        raise NotImplementedError

    @abstractmethod
    def get_owned_photo(self, firebase_uid: str, photo_id: int) -> PhotoRecord | None:
        raise NotImplementedError

    @abstractmethod
    def list_preview_photos(self, firebase_uid: str) -> list[PhotoRecord]:
        raise NotImplementedError

    @abstractmethod
    def create_preview_photo(
        self,
        user: UserRecord,
        original_filename: str,
        original_image_path: str,
        prepared_image_path: str,
        raw_mask_image_path: str,
        mask_image_path: str,
        operation_params: dict[str, Any],
    ) -> PhotoRecord:
        raise NotImplementedError

    @abstractmethod
    def claim_preview_for_generation(self, firebase_uid: str, photo_id: int) -> PhotoRecord:
        raise NotImplementedError

    @abstractmethod
    def mark_photo_completed(self, firebase_uid: str, photo_id: int, result_image_path: str) -> PhotoRecord:
        raise NotImplementedError

    @abstractmethod
    def mark_photo_preview(self, firebase_uid: str, photo_id: int) -> PhotoRecord:
        raise NotImplementedError

    @abstractmethod
    def delete_photo(self, firebase_uid: str, photo_id: int) -> None:
        raise NotImplementedError


class FirestorePhotoStore(AbstractPhotoStore):
    def __init__(self):
        self._client = firestore.client(app=_get_app())

    def _users(self):
        return self._client.collection("users")

    def _user_ref(self, firebase_uid: str):
        return self._users().document(firebase_uid)

    def _photos(self, firebase_uid: str):
        return self._user_ref(firebase_uid).collection("photos")

    def _user_from_data(self, data: dict[str, Any]) -> UserRecord:
        return UserRecord(
            id=int(data["id"]),
            firebase_uid=str(data["firebase_uid"]),
            email=str(data["email"]),
            display_name=data.get("display_name"),
            created_at=data["created_at"],
        )

    def _photo_from_data(self, data: dict[str, Any]) -> PhotoRecord:
        return PhotoRecord(
            id=int(data["id"]),
            user_id=int(data["user_id"]),
            original_filename=str(data["original_filename"]),
            original_image_path=str(data["original_image_path"]),
            prepared_image_path=data.get("prepared_image_path"),
            result_image_path=data.get("result_image_path"),
            raw_mask_image_path=data.get("raw_mask_image_path"),
            mask_image_path=data.get("mask_image_path"),
            status=PhotoStatus(data["status"]),
            operation_type=OperationType(data["operation_type"]),
            operation_params=data.get("operation_params"),
            created_at=data["created_at"],
        )

    def _user_payload(self, user: UserRecord, *, next_photo_id: int | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": user.id,
            "firebase_uid": user.firebase_uid,
            "email": user.email,
            "display_name": user.display_name,
            "created_at": user.created_at,
        }
        if next_photo_id is not None:
            payload["next_photo_id"] = next_photo_id
        return payload

    def _photo_payload(self, photo: PhotoRecord) -> dict[str, Any]:
        return {
            "id": photo.id,
            "user_id": photo.user_id,
            "original_filename": photo.original_filename,
            "original_image_path": photo.original_image_path,
            "prepared_image_path": photo.prepared_image_path,
            "result_image_path": photo.result_image_path,
            "raw_mask_image_path": photo.raw_mask_image_path,
            "mask_image_path": photo.mask_image_path,
            "status": photo.status.value,
            "operation_type": photo.operation_type.value,
            "operation_params": photo.operation_params,
            "created_at": photo.created_at,
        }

    def _get_user_snapshot(self, firebase_uid: str):
        return self._user_ref(firebase_uid).get()

    def sync_user(self, firebase_uid: str, email: str, display_name: str | None) -> UserRecord:
        return self.get_or_create_user(firebase_uid, email, display_name)

    def get_or_create_user(self, firebase_uid: str, email: str, display_name: str | None) -> UserRecord:
        user_ref = self._user_ref(firebase_uid)
        counters_ref = self._client.collection("_meta").document("counters")
        transaction = self._client.transaction()

        @firestore.transactional
        def _txn(transaction):
            snap = user_ref.get(transaction=transaction)
            if snap.exists:
                data = snap.to_dict() or {}
                updates: dict[str, Any] = {}
                if data.get("email") != email:
                    updates["email"] = email
                if data.get("display_name") != display_name:
                    updates["display_name"] = display_name
                if updates:
                    transaction.update(user_ref, updates)
                    data.update(updates)
                return self._user_from_data(data)

            counters_snap = counters_ref.get(transaction=transaction)
            counters = counters_snap.to_dict() or {}
            next_user_id = int(counters.get("next_user_id", 0)) + 1
            now = _utcnow()
            user = UserRecord(
                id=next_user_id,
                firebase_uid=firebase_uid,
                email=email,
                display_name=display_name,
                created_at=now,
            )
            transaction.set(counters_ref, {"next_user_id": next_user_id}, merge=True)
            transaction.set(user_ref, self._user_payload(user, next_photo_id=0))
            return user

        return _txn(transaction)

    def list_completed_photos(self, firebase_uid: str, skip: int, limit: int) -> tuple[list[PhotoRecord], int]:
        docs = self._photos(firebase_uid).order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        completed = [self._photo_from_data(doc.to_dict() or {}) for doc in docs if (doc.to_dict() or {}).get("status") == PhotoStatus.completed.value]
        total = len(completed)
        return completed[skip : skip + limit], total

    def get_owned_photo(self, firebase_uid: str, photo_id: int) -> PhotoRecord | None:
        snap = self._photos(firebase_uid).document(str(photo_id)).get()
        if not snap.exists:
            return None
        return self._photo_from_data(snap.to_dict() or {})

    def list_preview_photos(self, firebase_uid: str) -> list[PhotoRecord]:
        docs = self._photos(firebase_uid).stream()
        previews: list[PhotoRecord] = []
        for doc in docs:
            data = doc.to_dict() or {}
            if data.get("status") == PhotoStatus.preview.value:
                previews.append(self._photo_from_data(data))
        return previews

    def create_preview_photo(
        self,
        user: UserRecord,
        original_filename: str,
        original_image_path: str,
        prepared_image_path: str,
        raw_mask_image_path: str,
        mask_image_path: str,
        operation_params: dict[str, Any],
    ) -> PhotoRecord:
        user_ref = self._user_ref(user.firebase_uid)
        transaction = self._client.transaction()

        @firestore.transactional
        def _txn(transaction):
            snap = user_ref.get(transaction=transaction)
            if not snap.exists:
                raise ValueError("User not found while creating preview photo.")
            user_data = snap.to_dict() or {}
            next_photo_id = int(user_data.get("next_photo_id", 0)) + 1
            photo = PhotoRecord(
                id=next_photo_id,
                user_id=user.id,
                original_filename=original_filename,
                original_image_path=original_image_path,
                prepared_image_path=prepared_image_path,
                result_image_path=None,
                raw_mask_image_path=raw_mask_image_path,
                mask_image_path=mask_image_path,
                status=PhotoStatus.preview,
                operation_type=OperationType.edit_photo,
                operation_params=operation_params,
                created_at=_utcnow(),
            )
            transaction.update(user_ref, {"next_photo_id": next_photo_id})
            transaction.set(self._photos(user.firebase_uid).document(str(photo.id)), self._photo_payload(photo))
            return photo

        return _txn(transaction)

    def claim_preview_for_generation(self, firebase_uid: str, photo_id: int) -> PhotoRecord:
        photo_ref = self._photos(firebase_uid).document(str(photo_id))
        transaction = self._client.transaction()

        @firestore.transactional
        def _txn(transaction):
            snap = photo_ref.get(transaction=transaction)
            if not snap.exists:
                raise PhotoNotFoundError
            photo = self._photo_from_data(snap.to_dict() or {})
            if photo.status != PhotoStatus.preview:
                raise PhotoConflictError("Photo preview is already being generated.")
            transaction.update(photo_ref, {"status": PhotoStatus.generating.value})
            return replace(photo, status=PhotoStatus.generating)

        return _txn(transaction)

    def mark_photo_completed(self, firebase_uid: str, photo_id: int, result_image_path: str) -> PhotoRecord:
        photo = self.get_owned_photo(firebase_uid, photo_id)
        if photo is None:
            raise PhotoNotFoundError
        updated = replace(photo, result_image_path=result_image_path, status=PhotoStatus.completed)
        self._photos(firebase_uid).document(str(photo_id)).set(self._photo_payload(updated))
        return updated

    def mark_photo_preview(self, firebase_uid: str, photo_id: int) -> PhotoRecord:
        photo = self.get_owned_photo(firebase_uid, photo_id)
        if photo is None:
            raise PhotoNotFoundError
        updated = replace(photo, status=PhotoStatus.preview)
        self._photos(firebase_uid).document(str(photo_id)).set(self._photo_payload(updated))
        return updated

    def delete_photo(self, firebase_uid: str, photo_id: int) -> None:
        self._photos(firebase_uid).document(str(photo_id)).delete()


class InMemoryPhotoStore(AbstractPhotoStore):
    def __init__(self):
        self._users: dict[str, dict[str, Any]] = {}
        self._photos: dict[str, dict[int, PhotoRecord]] = {}
        self._next_user_id = 0

    def sync_user(self, firebase_uid: str, email: str, display_name: str | None) -> UserRecord:
        return self.get_or_create_user(firebase_uid, email, display_name)

    def get_or_create_user(self, firebase_uid: str, email: str, display_name: str | None) -> UserRecord:
        existing = self._users.get(firebase_uid)
        if existing is None:
            self._next_user_id += 1
            user = UserRecord(
                id=self._next_user_id,
                firebase_uid=firebase_uid,
                email=email,
                display_name=display_name,
                created_at=_utcnow(),
            )
            self._users[firebase_uid] = {"user": user, "next_photo_id": 0}
            self._photos[firebase_uid] = {}
            return replace(user)

        user = existing["user"]
        updated = replace(user, email=email, display_name=display_name)
        existing["user"] = updated
        return replace(updated)

    def list_completed_photos(self, firebase_uid: str, skip: int, limit: int) -> tuple[list[PhotoRecord], int]:
        photos = [
            replace(photo)
            for photo in sorted(
                self._photos.get(firebase_uid, {}).values(),
                key=lambda item: item.created_at,
                reverse=True,
            )
            if photo.status == PhotoStatus.completed
        ]
        total = len(photos)
        return photos[skip : skip + limit], total

    def get_owned_photo(self, firebase_uid: str, photo_id: int) -> PhotoRecord | None:
        photo = self._photos.get(firebase_uid, {}).get(photo_id)
        return replace(photo) if photo is not None else None

    def list_preview_photos(self, firebase_uid: str) -> list[PhotoRecord]:
        return [
            replace(photo)
            for photo in self._photos.get(firebase_uid, {}).values()
            if photo.status == PhotoStatus.preview
        ]

    def create_preview_photo(
        self,
        user: UserRecord,
        original_filename: str,
        original_image_path: str,
        prepared_image_path: str,
        raw_mask_image_path: str,
        mask_image_path: str,
        operation_params: dict[str, Any],
    ) -> PhotoRecord:
        meta = self._users[user.firebase_uid]
        meta["next_photo_id"] += 1
        photo = PhotoRecord(
            id=meta["next_photo_id"],
            user_id=user.id,
            original_filename=original_filename,
            original_image_path=original_image_path,
            prepared_image_path=prepared_image_path,
            result_image_path=None,
            raw_mask_image_path=raw_mask_image_path,
            mask_image_path=mask_image_path,
            status=PhotoStatus.preview,
            operation_type=OperationType.edit_photo,
            operation_params=operation_params,
            created_at=_utcnow(),
        )
        self._photos[user.firebase_uid][photo.id] = photo
        return replace(photo)

    def claim_preview_for_generation(self, firebase_uid: str, photo_id: int) -> PhotoRecord:
        photo = self._photos.get(firebase_uid, {}).get(photo_id)
        if photo is None:
            raise PhotoNotFoundError
        if photo.status != PhotoStatus.preview:
            raise PhotoConflictError("Photo preview is already being generated.")
        updated = replace(photo, status=PhotoStatus.generating)
        self._photos[firebase_uid][photo_id] = updated
        return replace(updated)

    def mark_photo_completed(self, firebase_uid: str, photo_id: int, result_image_path: str) -> PhotoRecord:
        photo = self._photos.get(firebase_uid, {}).get(photo_id)
        if photo is None:
            raise PhotoNotFoundError
        updated = replace(photo, status=PhotoStatus.completed, result_image_path=result_image_path)
        self._photos[firebase_uid][photo_id] = updated
        return replace(updated)

    def mark_photo_preview(self, firebase_uid: str, photo_id: int) -> PhotoRecord:
        photo = self._photos.get(firebase_uid, {}).get(photo_id)
        if photo is None:
            raise PhotoNotFoundError
        updated = replace(photo, status=PhotoStatus.preview)
        self._photos[firebase_uid][photo_id] = updated
        return replace(updated)

    def delete_photo(self, firebase_uid: str, photo_id: int) -> None:
        self._photos.get(firebase_uid, {}).pop(photo_id, None)
