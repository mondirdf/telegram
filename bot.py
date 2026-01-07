```python
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests

# ═══════════════════════════════════════════════════════════════════
# 🔧 إعدادات البوت
# ═══════════════════════════════════════════════════════════════════

BOT_TOKEN = "PUT_TELEGRAM_BOT_TOKEN"
EDGE_URL = "PUT_SUPABASE_EDGE_FUNCTION_URL"
SUPABASE_JWT = "PUT_SUPABASE_ANON_PUBLIC_JWT"

# ═══════════════════════════════════════════════════════════════════
# 📝 إعداد السجلات
# ═══════════════════════════════════════════════════════════════════

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 🔌 دالة استدعاء Edge Function
# ═══════════════════════════════════════════════════════════════════

def call_edge_function():
    """استدعاء Edge Function مباشرة بدون payload"""
    headers = {
        "Authorization": f"Bearer {SUPABASE_JWT}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(EDGE_URL, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "انتهت مهلة الاتصال بالخادم"}
    except requests.exceptions.ConnectionError:
        return {"error": "فشل الاتصال بالخادم"}
    except requests.exceptions.HTTPError as e:
        try:
            error_data = e.response.json()
            error_msg = error_data.get("error", f"خطأ في الخادم: {e.response.status_code}")
        except:
            error_msg = f"خطأ في الخادم: {e.response.status_code}"
        return {"error": error_msg}
    except Exception as e:
        return {"error": f"خطأ غير متوقع: {str(e)}"}

# ═══════════════════════════════════════════════════════════════════
# 🎯 أوامر البوت
# ═══════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر /start - رسالة الترحيب"""
    welcome_message = """
🎓 *مرحباً بك في بوت التخطيط الدراسي*

أنا هنا لمساعدتك في إنشاء جدول دراسي ذكي بناءً على تفضيلاتك ومهامك ✨

📋 *الأوامر المتاحة:*

/generate - إنشاء جدول دراسي جديد

🚀 ابدأ الآن بإنشاء جدولك!
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر /generate - إنشاء جدول دراسي"""
    await update.message.reply_text("⏳ جاري إنشاء الجدول الدراسي...")
    
    result = call_edge_function()
    
    # معالجة الأخطاء
    if "error" in result:
        await update.message.reply_text(f"❌ حدث خطأ:\n{result['error']}")
        return
    
    # التحقق من نجاح العملية
    if not result.get("ok"):
        error_msg = result.get("error", "فشل إنشاء الجدول")
        await update.message.reply_text(f"❌ {error_msg}")
        return
    
    # استخراج البيانات
    schedule = result.get("schedule", {})
    sessions = schedule.get("sessions", [])
    total_hours = schedule.get("totalPlannedHours", 0)
    utilization = schedule.get("utilizationRate", 0)
    sessions_count = len(sessions)
    
    # رسالة النجاح
    success_message = f"""
✅ *تم إنشاء الجدول بنجاح!*

📊 *الإحصائيات:*
• عدد الجلسات: {sessions_count}
• مجموع الساعات: {total_hours:.1f} ساعة
• معدل الاستخدام: {utilization:.1f}%

🎯 تم حفظ الجدول في قاعدة البيانات
"""
    await update.message.reply_text(success_message, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء العام"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        await update.message.reply_text(
            "⚠️ حدث خطأ غير متوقع\n"
            "الرجاء المحاولة مرة أخرى"
        )
    except:
        pass

# ═══════════════════════════════════════════════════════════════════
# 🚀 تشغيل البوت
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    """تشغيل البوت"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # تسجيل معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("generate", generate))
    
    # تسجيل معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    logger.info("🤖 البوت يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
```
