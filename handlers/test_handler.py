from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database as db
from keyboards import answer_kb, test_start_kb, main_menu_kb

router = Router()


class TestSession(StatesGroup):
    in_progress = State()


@router.callback_query(F.data.startswith("test_info_"))
async def test_info(callback: CallbackQuery):
    tid = int(callback.data.split("_")[2])
    test = db.get_test(tid)
    if not test:
        await callback.answer("Test topilmadi!", show_alert=True)
        return
    qc = db.count_questions(tid)
    time_txt = f"⏱ {test['time_limit']} daqiqa\n" if test["time_limit"] else ""
    text = (
        f"📝 <b>{test['title']}</b>\n\n"
        f"{test['description'] or ''}\n\n"
        f"❓ Savollar: <b>{qc} ta</b>\n"
        f"{time_txt}"
        f"✅ O'tish bali: <b>{test['pass_score']}%</b>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=test_start_kb(tid))


@router.callback_query(F.data.startswith("start_test_"))
async def start_test(callback: CallbackQuery, state: FSMContext):
    tid = int(callback.data.split("_")[2])
    questions = db.get_questions(tid)
    if not questions:
        await callback.answer("Bu testda savollar yo'q!", show_alert=True)
        return

    await state.set_state(TestSession.in_progress)
    await state.update_data(
        test_id=tid,
        questions=[dict(q) for q in questions],
        current=0,
        answers={},
        correct=0
    )
    test = db.get_test(tid)
    await callback.message.edit_text(
        f"🚀 <b>{test['title']}</b> boshlandi! ({len(questions)} ta savol)",
        parse_mode="HTML"
    )
    await send_question(callback.message, state, 0, [dict(q) for q in questions])


async def send_question(message, state: FSMContext, idx: int, questions: list):
    if idx >= len(questions):
        await finish_test(message, state)
        return
    q = questions[idx]
    opts = {"A": q["option_a"], "B": q["option_b"], "C": q["option_c"], "D": q["option_d"]}
    text = f"❓ <b>Savol {idx+1}/{len(questions)}</b>\n\n{q['question_text']}"
    await message.answer(text, parse_mode="HTML", reply_markup=answer_kb(idx, opts))


@router.callback_query(TestSession.in_progress, F.data.startswith("answer_"))
async def process_answer(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    q_idx = int(parts[1])
    selected = parts[2]

    data = await state.get_data()
    if q_idx != data["current"]:
        await callback.answer("Bu savol allaqachon javoblangan!", show_alert=True)
        return

    q = data["questions"][q_idx]
    is_correct = selected.upper() == q["correct_answer"].upper()
    correct = data["correct"] + (1 if is_correct else 0)
    answers = data["answers"]
    answers[str(q_idx)] = {"selected": selected, "correct": q["correct_answer"], "ok": is_correct}

    await state.update_data(current=q_idx + 1, correct=correct, answers=answers)

    feedback = "✅ To'g'ri!" if is_correct else f"❌ Noto'g'ri! To'g'ri: <b>{q['correct_answer']}</b>"
    if q.get("explanation"):
        feedback += f"\n\n💡 <i>{q['explanation']}</i>"
    await callback.message.edit_text(feedback, parse_mode="HTML")

    if q_idx + 1 < len(data["questions"]):
        await send_question(callback.message, state, q_idx + 1, data["questions"])
    else:
        await finish_test(callback.message, state)


async def finish_test(message, state: FSMContext):
    data = await state.get_data()
    test = db.get_test(data["test_id"])
    total = len(data["questions"])
    correct = data["correct"]
    score = round(correct / total * 100) if total else 0
    passed = score >= test["pass_score"]

    db.save_result(
        uid=message.chat.id,
        test_id=data["test_id"],
        correct=correct,
        total=total,
        answers=data["answers"],
        pass_score=test["pass_score"]
    )
    await state.clear()

    icon = "🎉" if passed else "😔"
    result = "✅ O'tdi!" if passed else "❌ O'tmadi"
    msg = "Tabriklaymiz! Muvaffaqiyatli yakunladingiz!" if passed else "Ko'proq o'qib, qaytadan urinib ko'ring!"

    await message.answer(
        f"{icon} <b>Test yakunlandi!</b>\n\n"
        f"📝 {test['title']}\n"
        f"✅ To'g'ri: {correct}/{total}\n"
        f"📊 Ball: <b>{score}%</b>\n"
        f"🎯 Natija: <b>{result}</b>\n\n"
        f"{msg}",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


@router.message(F.text == "📊 Natijalarim")
async def my_results(message: Message):
    results = db.get_user_results(message.from_user.id)
    if not results:
        await message.answer("📭 Hali hech qanday test yechilmagan.", reply_markup=main_menu_kb())
        return
    text = "📊 <b>Sizning natijalaringiz:</b>\n\n"
    for i, r in enumerate(results[:10], 1):
        icon = "✅" if r["passed"] else "❌"
        text += f"{i}. {icon} <b>{r['test_title']}</b> — {r['score']}% ({r['correct_answers']}/{r['total_questions']})\n"
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())
