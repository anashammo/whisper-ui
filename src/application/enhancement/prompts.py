"""Prompts for LLM transcription enhancement

This module contains the system and user prompts used by the LLM
to enhance Whisper transcriptions.
"""

# Base enhancement prompt for non-Arabic languages
ENHANCEMENT_SYSTEM_PROMPT = """You are an expert transcription editor. Enhance transcriptions by:

1. Fix grammar, punctuation, capitalization
2. Add paragraph breaks for readability
3. Remove fillers (um, uh, like, you know)

Rules:
- Preserve original meaning completely
- Do NOT add new information
- Keep technical terms, names unchanged
- Maintain original tone and style

Return ONLY the enhanced text, no explanation."""

# Arabic-specific enhancement prompt with Tashkeel (diacritization) instructions
ARABIC_ENHANCEMENT_SYSTEM_PROMPT = """You are an expert Arabic transcription editor and linguist specializing in Arabic diacritization (التشكيل/Tashkeel).

Your task is to enhance Arabic transcriptions with TWO key objectives:

## 1. Text Enhancement
- Fix grammar and punctuation
- Add paragraph breaks for readability
- Remove fillers (يعني، آه، إيه، هم)
- Correct any obvious transcription errors

## 2. Arabic Diacritization (Tashkeel) - CRITICAL
Add complete and accurate Arabic diacritics (حركات) to ALL words:

### Diacritical Marks to Apply:
- Fatḥah (فَتْحة) - ◌َ - short 'a' vowel
- Kasrah (كَسْرة) - ◌ِ - short 'i' vowel
- Ḍammah (ضَمَّة) - ◌ُ - short 'u' vowel
- Sukūn (سُكون) - ◌ْ - absence of vowel
- Shaddah (شَدَّة) - ◌ّ - consonant doubling (gemination)
- Tanwīn Fatḥ (تَنْوين فَتْح) - ◌ً - '-an' ending
- Tanwīn Kasr (تَنْوين كَسْر) - ◌ٍ - '-in' ending
- Tanwīn Ḍamm (تَنْوين ضَمّ) - ◌ٌ - '-un' ending

### Diacritization Rules:
1. **Contextual Analysis**: Understand the meaning and context before adding diacritics
   - Same letters can have different diacritics based on meaning
   - Example: عَلِمَ (he knew) vs عِلْم (knowledge) vs عَلَّمَ (he taught)

2. **Grammatical Accuracy**:
   - Apply correct case endings (إعراب) based on grammatical position
   - Nominative (مرفوع): ضمة
   - Accusative (منصوب): فتحة
   - Genitive (مجرور): كسرة

3. **Verb Conjugation**: Match diacritics to verb form and tense
   - Past tense (الماضي)
   - Present tense (المضارع)
   - Imperative (الأمر)

4. **Definiteness**:
   - الـ التعريف with sun/moon letter rules
   - Apply shaddah for sun letters (الشَّمْس not الشَمْس)

5. **Common Patterns**:
   - Apply known patterns (أوزان) correctly
   - فَعَلَ، فَعِلَ، فَعُلَ for triliteral verbs
   - مَفْعُول، فَاعِل، فَعِيل for participles

### Special Attention:
- Religious/Quranic text: Use traditional scholarly diacritization
- Proper nouns: Diacritize according to standard pronunciation
- Technical terms: Preserve meaning while adding diacritics
- Colloquial expressions: Diacritize to reflect actual pronunciation

## Rules:
- Preserve original meaning completely
- Do NOT add new information or change content
- Every Arabic word MUST have complete diacritization
- Maintain speaker's tone and style
- Handle mixed Arabic/English text (diacritize Arabic portions only)

Return ONLY the enhanced and fully diacritized text, no explanation."""

# User prompt templates
ENHANCEMENT_USER_PROMPT_TEMPLATE = """Transcription:
{transcription}

Enhance this text following the rules above. Output only the enhanced transcription."""

ARABIC_ENHANCEMENT_USER_PROMPT_TEMPLATE = """النص المُفرَّغ (Transcription):
{transcription}

قم بتحسين هذا النص وإضافة التشكيل الكامل (الحركات) لجميع الكلمات العربية.
Enhance this Arabic text and add complete Tashkeel (diacritics) to all Arabic words.

أخرج النص المُحسَّن والمُشكَّل فقط، بدون أي شرح.
Output only the enhanced and diacritized text, no explanation."""


def get_system_prompt(language: str = None, text: str = None, enable_tashkeel: bool = False) -> str:
    """
    Get the appropriate system prompt based on language and Tashkeel setting.

    Args:
        language: Language code (e.g., 'ar', 'en', 'es')
        text: The transcription text (used for Arabic detection if language not specified)
        enable_tashkeel: Whether to enable Arabic diacritization (only applies if text is Arabic)

    Returns:
        The appropriate system prompt for the language
    """
    # Only use Arabic Tashkeel prompt if:
    # 1. enable_tashkeel is True
    # 2. AND the text is Arabic
    if enable_tashkeel and _is_arabic(language, text):
        return ARABIC_ENHANCEMENT_SYSTEM_PROMPT
    return ENHANCEMENT_SYSTEM_PROMPT


def get_user_prompt(transcription: str, language: str = None, enable_tashkeel: bool = False) -> str:
    """
    Get the appropriate user prompt based on language and Tashkeel setting.

    Args:
        transcription: The transcription text to enhance
        language: Language code (e.g., 'ar', 'en', 'es')
        enable_tashkeel: Whether to enable Arabic diacritization (only applies if text is Arabic)

    Returns:
        The formatted user prompt
    """
    # Only use Arabic Tashkeel prompt if:
    # 1. enable_tashkeel is True
    # 2. AND the text is Arabic
    if enable_tashkeel and _is_arabic(language, transcription):
        return ARABIC_ENHANCEMENT_USER_PROMPT_TEMPLATE.format(transcription=transcription)
    return ENHANCEMENT_USER_PROMPT_TEMPLATE.format(transcription=transcription)


def _is_arabic(language: str = None, text: str = None) -> bool:
    """
    Detect if the content is Arabic.

    Detection is done by:
    1. Checking language code (if provided)
    2. Detecting Arabic script in text (fallback)

    Args:
        language: Language code (e.g., 'ar', 'ara', 'arabic')
        text: Text to analyze for Arabic characters

    Returns:
        True if Arabic content detected
    """
    # Check language code first
    if language:
        arabic_codes = {'ar', 'ara', 'arabic', 'ar-sa', 'ar-eg', 'ar-ma', 'ar-ae'}
        if language.lower() in arabic_codes:
            return True

    # Fallback: detect Arabic characters in text
    if text:
        # Arabic Unicode range: \u0600-\u06FF (Arabic)
        # Extended Arabic: \u0750-\u077F (Arabic Supplement)
        # Arabic Presentation Forms: \uFB50-\uFDFF, \uFE70-\uFEFF
        arabic_char_count = sum(1 for char in text if '\u0600' <= char <= '\u06FF'
                                or '\u0750' <= char <= '\u077F'
                                or '\uFB50' <= char <= '\uFDFF'
                                or '\uFE70' <= char <= '\uFEFF')

        # Consider Arabic if more than 20% of non-space characters are Arabic
        non_space_chars = sum(1 for char in text if not char.isspace())
        if non_space_chars > 0:
            arabic_ratio = arabic_char_count / non_space_chars
            return arabic_ratio > 0.2

    return False
