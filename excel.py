from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import ADMINS
from states.states import ExcelFSM
from database.engine import async_session
from database.models import Student
from keyboards.reply import admin_menu
from keyboards.buttons import BTN_EXCEL_UPLOAD
from utils.helpers import download_excel, safe_int

router = Router()


@router.message(F.text == BTN_EXCEL_UPLOAD, F.from_user.id.in_(ADMINS))
async def ask_excel(message: Message, state: FSMContext):
    await message.answer("📥 .xlsx faylni yuboring.\n"
                         "Ustunlar: <code>name, last_name, tel, group_id</code>")
    await state.set_state(ExcelFSM.file)


@router.message(ExcelFSM.file, F.document)
async def load_excel(message: Message, state: FSMContext):
    df, err = await download_excel(message)
    if err:
        await message.answer(err)
        return

    required = {"name", "last_name", "tel", "group_id"}
    if not required.issubset(set(df.columns)):
        await message.answer(f"❌ Ustunlar yetishmaydi. Kerak: {', '.join(required)}")
        await state.clear()
        return

    added, skipped = 0, 0
    async with async_session() as session:
        for _, row in df.iterrows():
            gid = safe_int(row["group_id"])
            name = str(row.get("name", "")).strip()
            last = str(row.get("last_name", "")).strip()
            if gid is None or not name or not last:
                skipped += 1
                continue
            session.add(Student(name=name, last_name=last,
                                tel=str(row.get("tel", "")).strip(),
                                group_id=gid, balance=0.0))
            added += 1
        await session.commit()

    await message.answer(f"✅ Qo'shildi: {added}\n⚠️ O'tkazib yuborildi: {skipped}",
                         reply_markup=admin_menu())
    await state.clear()


@router.message(ExcelFSM.file)
async def excel_invalid(message: Message):
    await message.answer("❌ Iltimos, .xlsx faylni yuboring.")
