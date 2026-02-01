"""
Сервис уведомлений.

Отправка уведомлений пользователям о новых объявлениях и сообщениях.
"""

from decimal import Decimal
from sqlalchemy import select, update as sql_update, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from loguru import logger

from database.models import Subscription, Ad, User


class NotificationService:
    """Сервис отправки уведомлений."""
    
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
    
    async def notify_new_ad(self, ad: Ad) -> int:
        """Уведомляет подписчиков о новом объявлении."""
        query = (
            select(Subscription)
            .where(Subscription.is_active == True)
            .where(Subscription.user_id != ad.owner_id)
        )
        result = await self.session.execute(query)
        subscriptions = result.scalars().all()
        
        sent_count = 0
        for sub in subscriptions:
            if not sub.matches_ad(ad):
                continue
            success = await self._send_notification(
                user_id=sub.user.telegram_id,
                text=f"🔔 <b>Новое объявление!</b>\n\n{ad.format_short()}"
            )
            if success:
                sent_count += 1
        return sent_count
    
    async def notify_ad_approved(self, ad: Ad) -> bool:
        """Уведомляет владельца об одобрении."""
        return await self._send_notification(
            user_id=ad.owner.telegram_id,
            text=f"✅ <b>Объявление одобрено!</b>\n\n📦 {ad.title}"
        )
    
    async def notify_ad_rejected(self, ad: Ad) -> bool:
        """Уведомляет владельца об отклонении."""
        return await self._send_notification(
            user_id=ad.owner.telegram_id,
            text=f"❌ <b>Объявление отклонено</b>\n\n📦 {ad.title}\n📝 Причина: {ad.rejection_reason}"
        )
    
    async def notify_admins(self, text: str) -> int:
        """Уведомляет всех админов."""
        query = select(User).where(User.is_admin == True)
        result = await self.session.execute(query)
        admins = result.scalars().all()
        
        sent_count = 0
        for admin in admins:
            if await self._send_notification(admin.telegram_id, text):
                sent_count += 1
        return sent_count
    
    async def notify_new_ad_for_moderation(self, ad: Ad) -> int:
        """Уведомляет админов о новом объявлении."""
        return await self.notify_admins(
            f"📬 <b>Новое объявление</b>\n\n📦 {ad.title}\n👤 {ad.owner.full_name}"
        )
    
    async def _send_notification(self, user_id: int, text: str) -> bool:
        """Отправляет уведомление."""
        try:
            await self.bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
            return True
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            logger.warning(f"Failed to send to {user_id}: {e}")
            return False


class SubscriptionService:
    """Сервис управления подписками."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        user_id: int,
        keywords: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        max_price: Optional[float] = None
    ) -> Subscription:
        """Создаёт подписку."""
        subscription = Subscription(
            user_id=user_id,
            keywords=keywords,
            category=category,
            location=location,
            max_price=Decimal(str(max_price)) if max_price else None,
            is_active=True
        )
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription
    
    async def get_user_subscriptions(self, user_id: int) -> list[Subscription]:
        """Получает подписки пользователя."""
        query = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def toggle_subscription(self, subscription_id: int, user_id: int) -> bool:
        """Переключает активность подписки."""
        query = select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.user_id == user_id
        )
        result = await self.session.execute(query)
        sub = result.scalar_one_or_none()
        
        if not sub:
            return False
        
        update_query = (
            sql_update(Subscription)
            .where(Subscription.id == subscription_id)
            .values(is_active=not sub.is_active)
        )
        await self.session.execute(update_query)
        await self.session.commit()
        return True
    
    async def delete_subscription(self, subscription_id: int, user_id: int) -> bool:
        """Удаляет подписку."""
        query = (
            sql_delete(Subscription)
            .where(Subscription.id == subscription_id)
            .where(Subscription.user_id == user_id)
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0