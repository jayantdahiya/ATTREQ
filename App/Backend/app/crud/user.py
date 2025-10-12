"""CRUD operations for User model."""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserCRUD:
    """CRUD operations for User model."""

    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> User | None:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            Optional[User]: User object or None if not found
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """
        Get user by email.

        Args:
            db: Database session
            email: User email address

        Returns:
            Optional[User]: User object or None if not found
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            obj_in: User creation data

        Returns:
            User: Created user object
        """
        # Check if user already exists
        existing_user = await self.get_by_email(db, obj_in.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Create user object
        user_data = obj_in.model_dump(exclude={"password"})
        user_data["password_hash"] = get_password_hash(obj_in.password)

        db_user = User(**user_data)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return db_user

    async def update(self, db: AsyncSession, db_obj: User, obj_in: UserUpdate) -> User:
        """
        Update user information.

        Args:
            db: Database session
            db_obj: Existing user object
            obj_in: Update data

        Returns:
            User: Updated user object
        """
        update_data = obj_in.model_dump(exclude_unset=True)

        if update_data:
            await db.execute(update(User).where(User.id == db_obj.id).values(**update_data))
            await db.commit()
            await db.refresh(db_obj)

        return db_obj

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> User | None:
        """
        Authenticate user with email and password.

        Args:
            db: Database session
            email: User email address
            password: Plain text password

        Returns:
            Optional[User]: User object if authentication successful, None otherwise
        """
        user = await self.get_by_email(db, email)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    async def update_last_login(self, db: AsyncSession, user: User) -> User:
        """
        Update user's last login timestamp.

        Args:
            db: Database session
            user: User object

        Returns:
            User: Updated user object
        """
        from datetime import datetime

        await db.execute(
            update(User).where(User.id == user.id).values(last_login=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(user)

        return user

    async def verify_user(self, db: AsyncSession, user: User) -> User:
        """
        Mark user as verified.

        Args:
            db: Database session
            user: User object

        Returns:
            User: Updated user object
        """
        await db.execute(update(User).where(User.id == user.id).values(is_verified=True))
        await db.commit()
        await db.refresh(user)

        return user

    async def deactivate_user(self, db: AsyncSession, user: User) -> User:
        """
        Deactivate user account.

        Args:
            db: Database session
            user: User object

        Returns:
            User: Updated user object
        """
        await db.execute(update(User).where(User.id == user.id).values(is_active=False))
        await db.commit()
        await db.refresh(user)

        return user


# Create instance for dependency injection
user_crud = UserCRUD()
