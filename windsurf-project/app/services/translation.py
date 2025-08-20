from flask import current_app
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    _HAS_ML = True
except Exception:
    # ML libraries are optional for server startup/preview
    pipeline = AutoTokenizer = AutoModelForSeq2SeqLM = None
    torch = None
    _HAS_ML = False

class TranslationService:
    def __init__(self):
        self.models = {}
        self.supported_languages = {
            'en': 'English',
            'hi': 'Hindi', 
            'ta': 'Tamil',
            'te': 'Telugu',
            'kn': 'Kannada',
            'bn': 'Bengali',
            'mr': 'Marathi',
            'gu': 'Gujarati'
        }
        # Lightweight key-based UI translations for immediate UI switching
        # Expand this catalog as needed
        self.catalog = {
            'en': {
                'worker_registration': 'Worker Registration',
                'client_registration': 'Client Registration',
                'login': 'Login',
                'email': 'Email',
                'full_name': 'Full Name',
                'phone_number': 'Phone Number',
                'password': 'Password',
                'language': 'Language',
                'confirm_password': 'Confirm Password',
                'state': 'State',
                'district': 'District',
                'select_state': 'Select State',
                'select_district': 'Select District',
                'city': 'City',
                'register': 'Register',
                'home': 'Home',
                'dashboard': 'Dashboard',
                'jobs': 'Jobs',
                'logout': 'Logout',
                'welcome': 'Welcome',
                'create_job': 'Create a Job',
                'create_new_job': 'Create a New Job',
                'job_title': 'Job Title',
                'description': 'Description',
                'budget_inr': 'Budget (INR)',
                'location': 'Location',
                'job_matches': 'Job Matches',
                'manage_skills': 'Manage Skills',
                'work_tags': 'Work Tags (comma separated)',
                'work_tags_placeholder': 'e.g. electrician, plumber, painter',
                'client_dashboard_intro': 'This is your client dashboard. Here you can post jobs, view applications, and connect with workers.',
                'worker_dashboard_intro': 'This is your worker dashboard. Here you can browse jobs, manage your skills, and track your applications.',
                'find_matching_jobs': 'Find Matching Jobs',
                'register_link': "Don't have an account? Register here",
                'signin_subtitle': 'Sign in to your KaamConnect account',
                'email_phone_placeholder': 'Enter your email or phone number',
                'password_placeholder': 'Enter your password',
                'remember_me': 'Remember me',
                'forgot_password': 'Forgot your password?'
            },
            'hi': {
                'worker_registration': 'कार्यकर्ता पंजीकरण',
                'client_registration': 'क्लाइंट पंजीकरण',
                'login': 'लॉगिन',
                'email': 'ईमेल',
                'full_name': 'पूरा नाम',
                'phone_number': 'फ़ोन नंबर',
                'password': 'पासवर्ड',
                'language': 'भाषा',
                'confirm_password': 'पासवर्ड की पुष्टि करें',
                'state': 'राज्य',
                'district': 'ज़िला',
                'select_state': 'राज्य चुनें',
                'select_district': 'ज़िला चुनें',
                'city': 'शहर',
                'register': 'पंजीकरण',
                'home': 'होम',
                'dashboard': 'डैशबोर्ड',
                'jobs': 'नौकरियां',
                'logout': 'लॉगआउट',
                'welcome': 'स्वागत है',
                'create_job': 'नौकरी बनाएं',
                'create_new_job': 'नई नौकरी बनाएं',
                'job_title': 'नौकरी का शीर्षक',
                'description': 'विवरण',
                'budget_inr': 'बजट (₹)',
                'location': 'स्थान',
                'job_matches': 'नौकरी मिलान',
                'manage_skills': 'कौशल प्रबंधन',
                'work_tags': 'कार्य टैग (अल्पविराम से अलग)',
                'work_tags_placeholder': 'जैसे इलेक्ट्रिशियन, प्लंबर, पेंटर',
                'client_dashboard_intro': 'यह आपका क्लाइंट डैशबोर्ड है। यहाँ आप नौकरियां पोस्ट कर सकते हैं, आवेदनों को देख सकते हैं, और कार्यकर्ताओं से जुड़ सकते हैं।',
                'worker_dashboard_intro': 'यह आपका वर्कर डैशबोर्ड है। यहाँ आप नौकरियां देख सकते हैं, अपने कौशल प्रबंधित कर सकते हैं, और अपने आवेदनों को ट्रैक कर सकते हैं।',
                'find_matching_jobs': 'मिलती-जुलती नौकरियां खोजें',
                'register_link': 'क्या आपका खाता नहीं है? यहाँ पंजीकरण करें',
                'signin_subtitle': 'अपने KaamConnect खाते में साइन इन करें',
                'email_phone_placeholder': 'अपना ईमेल या फ़ोन नंबर दर्ज करें',
                'password_placeholder': 'अपना पासवर्ड दर्ज करें',
                'remember_me': 'मुझे याद रखें',
                'forgot_password': 'क्या आप पासवर्ड भूल गए?'
            },
            'ta': {
                'worker_registration': 'தொழிலாளர் பதிவு',
                'client_registration': 'வாடிக்கையாளர் பதிவு',
                'login': 'உள்நுழை',
                'email': 'மின்னஞ்சல்',
                'full_name': 'முழுப்பெயர்',
                'phone_number': 'தொலைபேசி எண்',
                'password': 'கடவுச்சொல்',
                'language': 'மொழி',
                'confirm_password': 'கடவுச்சொல்லை உறுதிப்படுத்தவும்',
                'state': 'மாநிலம்',
                'district': 'மாவட்டம்',
                'select_state': 'மாநிலத்தை தேர்ந்தெடுக்கவும்',
                'select_district': 'மாவட்டத்தை தேர்ந்தெடுக்கவும்',
                'city': 'நகர்',
                'register': 'பதிவு',
                'home': 'முகப்பு',
                'dashboard': 'டாஷ்போர்டு',
                'jobs': 'வேலைகள்',
                'logout': 'வெளியேறு',
                'welcome': 'வரவேற்கிறோம்',
                'create_job': 'வேலை உருவாக்கு',
                'create_new_job': 'புதிய வேலை உருவாக்கு',
                'job_title': 'வேலை தலைப்பு',
                'description': 'விளக்கம்',
                'budget_inr': 'பட்ஜெட் (₹)',
                'location': 'இடம்',
                'job_matches': 'வேலை பொருத்தங்கள்',
                'manage_skills': 'திறன்கள் மேலாண்மை',
                'work_tags': 'வேலை குறிச்சொற்கள் (கமா பிரிக்கப்பட்டது)',
                'work_tags_placeholder': 'உ.தா. எலக்ட்ரீஷியன், பிளம்பர், பெயிண்டர்',
                'client_dashboard_intro': 'இது உங்கள் வாடிக்கையாளர் டாஷ்போர்டு. இங்கே நீங்கள் வேலைகளைப் பதிவிடலாம், விண்ணப்பங்களைப் பார்க்கலாம் மற்றும் தொழிலாளர்களுடன் இணைக்கலாம்.',
                'worker_dashboard_intro': 'இது உங்கள் தொழிலாளர் டாஷ்போர்டு. இங்கே நீங்கள் வேலைகளை உலாவலாம், உங்கள் திறன்களை நிர்வகிக்கலாம் மற்றும் உங்கள் விண்ணப்பங்களை கண்காணிக்கலாம்.',
                'find_matching_jobs': 'பொருத்தமான வேலைகளை கண்டறி',
                'register_link': 'கணக்கு இல்லையா? இங்கே பதிவு செய்யவும்',
                'signin_subtitle': 'உங்கள் KaamConnect கணக்கில் உள்நுழைக',
                'email_phone_placeholder': 'உங்கள் மின்னஞ்சல் அல்லது தொலைபேசி எண்ணை உள்ளிடவும்',
                'password_placeholder': 'உங்கள் கடவுச்சொல்லை உள்ளிடவும்',
                'remember_me': 'என்னை நினைவில் காக்கவும்',
                'forgot_password': 'கடவுச்சொல்லை மறந்துவிட்டீர்களா?'
            },
            'te': {
                'worker_registration': 'కార్మికుల నమోదు',
                'client_registration': 'క్లయింట్ నమోదు',
                'login': 'లాగిన్',
                'email': 'ఈమెయిల్',
                'full_name': 'పూర్తి పేరు',
                'phone_number': 'ఫోన్ నంబర్',
                'password': 'పాస్‌వర్డ్',
                'language': 'భాష',
                'confirm_password': 'పాస్‌వర్డ్ నిర్ధారించండి',
                'state': 'రాష్ట్రం',
                'district': 'జిల్లా',
                'select_state': 'రాష్ట్రాన్ని ఎంచుకోండి',
                'select_district': 'జిల్లాను ఎంచుకోండి',
                'city': 'నగరం',
                'register': 'నమోదు',
                'home': 'హోమ్',
                'dashboard': 'డాష్‌బోర్డ్',
                'jobs': 'ఉద్యోగాలు',
                'logout': 'లాగౌట్',
                'welcome': 'స్వాగతం',
                'create_job': 'ఉద్యోగం సృష్టించండి',
                'create_new_job': 'కొత్త ఉద్యోగం సృష్టించండి',
                'job_title': 'ఉద్యోగ శీర్షిక',
                'description': 'వివరణ',
                'budget_inr': 'బడ్జెట్ (₹)',
                'location': 'ప్రదేశం',
                'job_matches': 'ఉద్యోగ సరిపోలికలు',
                'manage_skills': 'నైపుణ్యాలు నిర్వహించండి',
                'work_tags': 'పని ట్యాగ్లు (కామాలతో విడదీయండి)',
                'work_tags_placeholder': 'ఉదా. ఎలక్ట్రీషియన్, ప్లంబర్, పెయింటర్',
                'client_dashboard_intro': 'ఇది మీ క్లయింట్ డాష్‌బోర్డ్. ఇక్కడ మీరు పనులను పోస్ట్ చేయవచ్చు, దరఖాస్తులను చూడవచ్చు మరియు కార్మికులతో కలవచ్చు.',
                'worker_dashboard_intro': 'ఇది మీ కార్మికుల డాష్‌బోర్డ్. ఇక్కడ మీరు ఉద్యోగాలను బ్రౌజ్ చేయవచ్చు, మీ నైపుణ్యాలను నిర్వహించవచ్చు మరియు దరఖాస్తులను ట్రాక్ చేయవచ్చు.',
                'find_matching_jobs': 'సరిపోలే ఉద్యోగాలను కనుగొనండి',
                'register_link': 'ఖాతా లేదా? ఇక్కడ నమోదు చేసుకోండి',
                'signin_subtitle': 'మీ KaamConnect ఖాతాలో సైన్ ఇన్ చేయండి',
                'email_phone_placeholder': 'మీ ఇమెయిల్ లేదా ఫోన్ నంబర్‌ని నమోదు చేయండి',
                'password_placeholder': 'మీ పాస్‌వర్డ్‌ను నమోదు చేయండి',
                'remember_me': 'నన్ను గుర్తుంచుకో',
                'forgot_password': 'మీ పాస్‌వర్డ్‌ను మర్చిపోయారా?'
            },
            'kn': {
                'worker_registration': 'ಕಾರ್ಮಿಕ ನೋಂದಣಿ',
                'client_registration': 'ಗ್ರಾಹಕ ನೋಂದಣಿ',
                'login': 'ಲಾಗಿನ್',
                'email': 'ಇಮೇಲ್',
                'full_name': 'ಪೂರ್ಣ ಹೆಸರು',
                'phone_number': 'ಫೋನ್ ಸಂಖ್ಯೆ',
                'password': 'ಪಾಸ್ವರ್ಡ್',
                'language': 'ಭಾಷೆ',
                'confirm_password': 'ಪಾಸ್ವರ್ಡ್ ದೃಢೀಕರಿಸಿ',
                'state': 'ರಾಜ್ಯ',
                'district': 'ಜಿಲ್ಲೆ',
                'select_state': 'ರಾಜ್ಯವನ್ನು ಆಯ್ಕೆಮಾಡಿ',
                'select_district': 'ಜಿಲ್ಲೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ',
                'city': 'ನಗರ',
                'register': 'ನೋಂದಣಿ',
                'home': 'ಮುಖಪುಟ',
                'dashboard': 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
                'jobs': 'ಕೆಲಸಗಳು',
                'logout': 'ಲಾಗ್ ಔಟ್',
                'welcome': 'ಸ್ವಾಗತ',
                'create_job': 'ಕೆಲಸ ರಚಿಸಿ',
                'create_new_job': 'ಹೊಸ ಕೆಲಸ ರಚಿಸಿ',
                'job_title': 'ಕೆಲಸದ ಶೀರ್ಷಿಕೆ',
                'description': 'ವಿವರಣೆ',
                'budget_inr': 'ಬಜೆಟ್ (₹)',
                'location': 'ಸ್ಥಳ',
                'job_matches': 'ಕೆಲಸ ಹೊಂದಾಣಿಕೆಗಳು',
                'manage_skills': 'ನಿಪುಣತೆಗಳನ್ನು ನಿರ್ವಹಿಸಿ',
                'work_tags': 'ಕೆಲಸದ ಟ್ಯಾಗ್ಗಳು (ಕಾಮಾಗಳಿಂದ ಬೇರ್ಪಡಿಸಿ)',
                'work_tags_placeholder': 'ಉದಾ. ಎಲೆಕ್ಟ್ರಿಷಿಯನ್, ಪ್ಲಂಬರ್, ಪೇಂಟರ್',
                'client_dashboard_intro': 'ಇದು ನಿಮ್ಮ ಗ್ರಾಹಕ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್. ಇಲ್ಲಿ ನೀವು ಕೆಲಸಗಳನ್ನು ಪೋಸ್ಟ್ ಮಾಡಬಹುದು, ಅರ್ಜಿಗಳನ್ನು ನೋಡಬಹುದು ಮತ್ತು ಕಾರ್ಮಿಕರೊಂದಿಗೆ ಸಂಪರ್ಕಿಸಬಹುದು.',
                'worker_dashboard_intro': 'ಇದು ನಿಮ್ಮ ಕಾರ್ಮಿಕರ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್. ಇಲ್ಲಿ ನೀವು ಕೆಲಸಗಳನ್ನು ಬ್ರೌಸ್ ಮಾಡಬಹುದು, ನಿಮ್ಮ ನಿಪುಣತೆಗಳನ್ನು ನಿರ್ವಹಿಸಬಹುದು ಮತ್ತು ಅರ್ಜಿಗಳನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಬಹುದು.',
                'find_matching_jobs': 'ಹೊಂದುವ ಕೆಲಸಗಳನ್ನು ಹುಡುಕಿ',
                'register_link': 'ಖಾತೆ ಇಲ್ಲವೇ? ಇಲ್ಲಿ ನೋಂದಣಿ ಮಾಡಿ',
                'signin_subtitle': 'ನಿಮ್ಮ KaamConnect ಖಾತೆಗೆ ಸೈನ್ ಇನ್ ಮಾಡಿ',
                'email_phone_placeholder': 'ನಿಮ್ಮ ಇಮೇಲ್ ಅಥವಾ ಫೋನ್ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ',
                'password_placeholder': 'ನಿಮ್ಮ ಪಾಸ್‌ವರ್ಡ್ ನಮೂದಿಸಿ',
                'remember_me': 'ನನ್ನನ್ನು ನೆನಪಿಡಿ',
                'forgot_password': 'ನಿಮ್ಮ ಪಾಸ್‌ವರ್ಡ್ ಮರೆತಿರಾ?'
            },
            'bn': {
                'worker_registration': 'শ্রমিক নিবন্ধন',
                'client_registration': 'ক্লায়েন্ট নিবন্ধন',
                'login': 'লগইন',
                'email': 'ইমেল',
                'full_name': 'পূর্ণ নাম',
                'phone_number': 'ফোন নম্বর',
                'password': 'পাসওয়ার্ড',
                'language': 'ভাষা',
                'confirm_password': 'পাসওয়ার্ড নিশ্চিত করুন',
                'state': 'রাজ্য',
                'district': 'জেলা',
                'select_state': 'রাজ্য নির্বাচন করুন',
                'select_district': 'জেলা নির্বাচন করুন',
                'city': 'শহর',
                'register': 'নিবন্ধন',
                'home': 'হোম',
                'dashboard': 'ড্যাশবোর্ড',
                'jobs': 'চাকরি',
                'logout': 'লগআউট',
                'welcome': 'স্বাগতম',
                'create_job': 'চাকরি তৈরি করুন',
                'create_new_job': 'নতুন চাকরি তৈরি করুন',
                'job_title': 'চাকরির শিরোনাম',
                'description': 'বিস্তারিত',
                'budget_inr': 'বাজেট (₹)',
                'location': 'অবস্থান',
                'job_matches': 'চাকরির মিল',
                'manage_skills': 'দক্ষতা পরিচালনা করুন',
                'work_tags': 'কাজের ট্যাগ (কমা দ্বারা পৃথক)',
                'work_tags_placeholder': 'যেমন ইলেকট্রিশিয়ান, প্লাম্বার, পেইন্টার',
                'client_dashboard_intro': 'এটি আপনার ক্লায়েন্ট ড্যাশবোর্ড। এখানে আপনি চাকরি পোস্ট করতে পারেন, আবেদনগুলি দেখতে পারেন এবং শ্রমিকদের সাথে সংযোগ স্থাপন করতে পারেন।',
                'worker_dashboard_intro': 'এটি আপনার শ্রমিক ড্যাশবোর্ড। এখানে আপনি চাকরি ব্রাউজ করতে পারেন, দক্ষতা পরিচালনা করতে পারেন এবং আবেদনগুলি ট্র্যাক করতে পারেন।',
                'find_matching_jobs': 'মিল আছে এমন চাকরি খুঁজুন',
                'register_link': 'অ্যাকাউন্ট নেই? এখানে নিবন্ধন করুন',
                'signin_subtitle': 'আপনার KaamConnect অ্যাকাউন্টে সাইন ইন করুন',
                'email_phone_placeholder': 'আপনার ইমেল বা ফোন নম্বর লিখুন',
                'password_placeholder': 'আপনার পাসওয়ার্ড লিখুন',
                'remember_me': 'আমাকে মনে রাখুন',
                'forgot_password': 'পাসওয়ার্ড ভুলে গেছেন?'
            },
            'mr': {
                'worker_registration': 'कामगार नोंदणी',
                'client_registration': 'ग्राहक नोंदणी',
                'login': 'लॉगिन',
                'email': 'ईमेल',
                'full_name': 'पूर्ण नाव',
                'phone_number': 'फोन नंबर',
                'password': 'पासवर्ड',
                'language': 'भाषा',
                'confirm_password': 'पासवर्डची पुष्टी करा',
                'state': 'राज्य',
                'district': 'जिल्हा',
                'select_state': 'राज्य निवडा',
                'select_district': 'जिल्हा निवडा',
                'city': 'शहर',
                'register': 'नोंदणी',
                'home': 'मुखपृष्ठ',
                'dashboard': 'डॅशबोर्ड',
                'jobs': 'नोकऱ्या',
                'logout': 'लॉगआउट',
                'welcome': 'स्वागत',
                'create_job': 'नोकरी तयार करा',
                'create_new_job': 'नवीन नोकरी तयार करा',
                'job_title': 'नोकरी शीर्षक',
                'description': 'वर्णन',
                'budget_inr': 'बजेट (₹)',
                'location': 'स्थान',
                'job_matches': 'नोकरी जुळणी',
                'manage_skills': 'कौशल्ये व्यवस्थापित करा',
                'work_tags': 'कामाच्या टॅग्स (स्वल्पविरामाने वेगळे)',
                'work_tags_placeholder': 'उदा. इलेक्ट्रिशियन, प्लंबर, पेंटर',
                'client_dashboard_intro': 'हा तुमचा क्लायंट डॅशबोर्ड आहे. येथे तुम्ही नोकऱ्या पोस्ट करू शकता, अर्ज पाहू शकता आणि कामगारांशी जोडू शकता.',
                'worker_dashboard_intro': 'हा तुमचा कामगार डॅशबोर्ड आहे. येथे तुम्ही नोकऱ्या पाहू शकता, तुमची कौशल्ये व्यवस्थापित करू शकता आणि अर्जांचा मागोवा ठेवू शकता.',
                'find_matching_jobs': 'जुळणाऱ्या नोकऱ्या शोधा',
                'register_link': 'खाते नाही? येथे नोंदणी करा',
                'signin_subtitle': 'तुमच्या KaamConnect खात्यात साइन इन करा',
                'email_phone_placeholder': 'आपला ईमेल किंवा फोन नंबर प्रविष्ट करा',
                'password_placeholder': 'आपला पासवर्ड प्रविष्ट करा',
                'remember_me': 'मला लक्षात ठेवा',
                'forgot_password': 'आपला पासवर्ड विसरलात का?'
            },
            'gu': {
                'worker_registration': 'મજૂર નોંધણી',
                'client_registration': 'ગ્રાહક નોંધણી',
                'login': 'લોગિન',
                'email': 'ઈમેલ',
                'full_name': 'પૂર્ણ નામ',
                'phone_number': 'ફોન નંબર',
                'password': 'પાસવર્ડ',
                'language': 'ભાષા',
                'confirm_password': 'પાસવર્ડની પુષ્ટિ કરો',
                'state': 'રાજ્ય',
                'district': 'જિલ્લો',
                'select_state': 'રાજ્ય પસંદ કરો',
                'select_district': 'જિલ્લો પસંદ કરો',
                'city': 'શહેર',
                'register': 'નોંધણી',
                'home': 'હોમ',
                'dashboard': 'ડેશબોર્ડ',
                'jobs': 'નોકરીઓ',
                'logout': 'લોગઆઉટ',
                'welcome': 'સ્વાગત છે',
                'create_job': 'નોકરી બનાવો',
                'create_new_job': 'નવી નોકરી બનાવો',
                'job_title': 'નોકરી શીર્ષક',
                'description': 'વર્ણન',
                'budget_inr': 'બજેટ (₹)',
                'location': 'સ્થાન',
                'job_matches': 'નોકરી મેળ',
                'manage_skills': 'કૌશલ્ય મેનેજ કરો',
                'work_tags': 'કામના ટેગ્સ (કામાથી અલગ)',
                'work_tags_placeholder': 'દા.ત. ઇલેક્ટ્રીશિયન, પ્લમ્બર, પેઇન્ટર',
                'client_dashboard_intro': 'આ તમારું ક્લાયન્ટ ડેશબોર્ડ છે. અહીં તમે નોકરીઓ પોસ્ટ કરી શકો છો, અરજીઓ જોઈ શકો છો અને મજૂરો સાથે જોડાઈ શકો છો.',
                'worker_dashboard_intro': 'આ તમારું મજૂર ડેશબોર્ડ છે. અહીં તમે નોકરીઓ બ્રાઉઝ કરી શકો છો, તમારી કૌશલ્યો મેનેજ કરી શકો છો અને અરજીઓ ટ્રેક કરી શકો છો.',
                'find_matching_jobs': 'મેળ ખાતી નોકરીઓ શોધો',
                'register_link': 'ખાતું નથી? અહીં નોંધણી કરો',
                'signin_subtitle': 'તમારા KaamConnect ખાતામાં સાઇન ઇન કરો',
                'email_phone_placeholder': 'તમારો ઈમેલ અથવા ફોન નંબર દાખલ કરો',
                'password_placeholder': 'તમારો પાસવર્ડ દાખલ કરો',
                'remember_me': 'મને યાદ રાખો',
                'forgot_password': 'તમે પાસવર્ડ ભૂલી ગયા છો?'
            }
            # Add more languages similarly (te, kn, bn, mr, gu)
        }

    def translate_key(self, key: str, target_lang: str, **kwargs) -> str:
        """Translate a UI key to the target language using the catalog.
        Falls back to English, then the key itself. Supports simple formatting.
        """
        try:
            target = (self.catalog.get(target_lang) or {}).get(key)
            if not target:
                target = (self.catalog.get('en') or {}).get(key) or key
            if kwargs:
                return target.format(**kwargs)
            return target
        except Exception:
            return key
        
    def load_model(self, source_lang, target_lang):
        """Load translation model for specific language pair"""
        if not _HAS_ML:
            # Skip model loading when ML libs are unavailable
            try:
                current_app.logger.warning("ML libraries not available; translation model will not be loaded for preview.")
            except Exception:
                pass
            return None
        model_key = f"{source_lang}_{target_lang}"
        
        if model_key not in self.models:
            try:
                # Use IndicTrans2 for Indian language translations
                if source_lang in ['hi', 'ta', 'te', 'kn', 'bn', 'mr', 'gu'] or target_lang in ['hi', 'ta', 'te', 'kn', 'bn', 'mr', 'gu']:
                    model_name = "ai4bharat/indictrans2-indic-en-1B"
                    if target_lang != 'en':
                        model_name = "ai4bharat/indictrans2-en-indic-1B"
                else:
                    # Use mBART for other translations
                    model_name = "facebook/mbart-large-50-many-to-many-mmt"
                
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                
                self.models[model_key] = {
                    'tokenizer': tokenizer,
                    'model': model,
                    'pipeline': pipeline('translation', model=model, tokenizer=tokenizer)
                }
            except Exception as e:
                current_app.logger.error(f"Error loading translation model {model_key}: {str(e)}")
                return None
                
        return self.models.get(model_key)
    
    def translate_text(self, text, source_lang, target_lang):
        """Translate text from source language to target language"""
        if not _HAS_ML:
            return text
        if source_lang == target_lang:
            return text
            
        model_info = self.load_model(source_lang, target_lang)
        if not model_info:
            return text  # Return original text if translation fails
            
        try:
            # Prepare input based on model type
            if 'indictrans' in str(model_info['model']):
                # IndicTrans2 specific formatting
                if source_lang != 'en':
                    text = f"{source_lang}: {text}"
                
                inputs = model_info['tokenizer'](text, return_tensors="pt", padding=True, truncation=True)
                
                with torch.no_grad():
                    outputs = model_info['model'].generate(**inputs, max_length=512)
                
                translated = model_info['tokenizer'].decode(outputs[0], skip_special_tokens=True)
            else:
                # mBART translation
                result = model_info['pipeline'](text, src_lang=source_lang, tgt_lang=target_lang)
                translated = result[0]['translation_text']
                
            return translated
            
        except Exception as e:
            current_app.logger.error(f"Translation error: {str(e)}")
            return text  # Return original text if translation fails
    
    def detect_language(self, text):
        """Detect the language of given text"""
        try:
            # Simple language detection based on script
            # This is a basic implementation - in production, use a proper language detection library
            
            # Check for Devanagari script (Hindi, Marathi)
            if any('\u0900' <= char <= '\u097F' for char in text):
                return 'hi'  # Default to Hindi for Devanagari
            
            # Check for Tamil script
            elif any('\u0B80' <= char <= '\u0BFF' for char in text):
                return 'ta'
            
            # Check for Telugu script
            elif any('\u0C00' <= char <= '\u0C7F' for char in text):
                return 'te'
            
            # Check for Kannada script
            elif any('\u0C80' <= char <= '\u0CFF' for char in text):
                return 'kn'
            
            # Check for Bengali script
            elif any('\u0980' <= char <= '\u09FF' for char in text):
                return 'bn'
            
            # Check for Gujarati script
            elif any('\u0A80' <= char <= '\u0AFF' for char in text):
                return 'gu'
            
            # Default to English
            else:
                return 'en'
                
        except Exception as e:
            current_app.logger.error(f"Language detection error: {str(e)}")
            return 'en'  # Default to English
    
    def get_supported_languages(self):
        """Get list of supported languages"""
        return self.supported_languages

# Global translation service instance
translation_service = TranslationService()
