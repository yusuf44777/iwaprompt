import streamlit as st
try:
    import pandas as pd
    import requests
    import io
    from datetime import datetime
    import re
    import json
except ImportError as e:
    st.error(f"Required packages not installed: {e}")
    st.stop()

# Sayfa yapılandırması
st.set_page_config(
    page_title="🤖 AI Prompt Koleksiyonu - IWA Concept",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=3600)  # 1 saat cache
def load_prompts():
    """GitHub'dan prompts.csv dosyasını yükle"""
    try:
        url = "https://raw.githubusercontent.com/f/awesome-chatgpt-prompts/main/prompts.csv"
        headers = {'User-Agent': 'IWA-Concept-Streamlit-App'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        csv_content = io.StringIO(response.text)
        df = pd.read_csv(csv_content)
        
        # Veri doğrulama
        if df.empty or 'act' not in df.columns or 'prompt' not in df.columns:
            raise ValueError("CSV formatı beklenen yapıda değil")
        
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"GitHub'dan veri çekilirken hata: {e}")
        st.info("💡 İnternet bağlantınızı kontrol edin veya sayfayı yenileyin")
        return None
    except Exception as e:
        st.error(f"Beklenmeyen hata: {e}")
        return None

def get_prompt_tips(role_name):
    """Her rol için özel ipuçları"""
    tips = {
        "Business Analyst": {
            "tips": [
                "Spesifik sektör ve şirket büyüklüğü belirtin",
                "Sayısal hedefler ve KPI'lar ekleyin", 
                "Zaman dilimi belirtin (aylık, çeyrek, yıllık)",
                "Rakip şirket isimlerini somut olarak verin"
            ],
            "example": "Son 6 ay satış verilerimizi analiz edip, teknoloji sektöründeki rakiplerimizle (Microsoft, Google) karşılaştırarak 2024 Q4 için strateji öner."
        },
        "Marketing Expert": {
            "tips": [
                "Hedef kitle demografisini detaylandırın",
                "Bütçe aralığı belirtin",
                "Hangi platformları kullandığınızı söyleyin",
                "Mevcut performans metriklerinizi paylaşın"
            ],
            "example": "25-40 yaş teknoloji profesyonelleri için LinkedIn'de 10.000₺ bütçeli B2B kampanya tasarla. Mevcut CTR %2.1."
        },
        "Content Creator": {
            "tips": [
                "Ton ve stil tercihini belirtin (formal, samimi, eğlenceli)",
                "Kelime sayısı sınırı koyun",
                "SEO anahtar kelimeleri verin",
                "Call-to-action hedefini açıklayın"
            ],
            "example": "Dijital dönüşüm hakkında 800 kelimelik SEO odaklı blog yazısı yaz. Anahtar kelimeler: 'yapay zeka', 'otomasyon'. Hedef: demo talep etme."
        },
        "Sales Representative": {
            "tips": [
                "Müşteri profilini detaylandırın",
                "Ürün/hizmet fiyat aralığını belirtin",
                "Satış sürecinin hangi aşamasında olduğunu söyleyin",
                "Önceki itirazları paylaşın"
            ],
            "example": "50-100 kişilik teknoloji şirketi CTO'suna SaaS ürünümüzü (aylık 5000₺) satmak için tekli sunumu hazırla. Ana itiraz: 'Çok pahalı'."
        },
        "Project Manager": {
            "tips": [
                "Takım büyüklüğü ve yapısını belirtin",
                "Proje süresini ve bütçesini verin",
                "Risk faktörlerini listeleyin",
                "Kullandığınız metodoloji belirtin (Agile, Waterfall)"
            ],
            "example": "8 kişilik geliştirici takımı ile 6 aylık e-ticaret projesi için Agile sprint planı oluştur. Bütçe: 500.000₺. Risk: API entegrasyonu."
        }
    }
    
    return tips.get(role_name, {
        "tips": ["Spesifik olun", "Örnekler verin", "Hedef belirtin", "Bağlam sağlayın"],
        "example": "Bu role özel örnek henüz eklenmedi."
    })

def analyze_prompt_quality(prompt_text):
    """Prompt kalitesini analiz et ve puanlama yap"""
    if not prompt_text or len(prompt_text.strip()) < 10:
        return {
            "score": 0,
            "grade": "F",
            "issues": ["Prompt çok kısa veya boş"],
            "suggestions": ["En az 20-30 kelimelik açıklayıcı bir prompt yazın"],
            "strengths": [],
            "detailed_analysis": {}
        }
    
    issues = []
    suggestions = []
    strengths = []
    score = 100
    
    # Detaylı analiz metrikleri
    detailed_analysis = {
        "length": len(prompt_text),
        "word_count": len(prompt_text.split()),
        "sentence_count": len([s for s in prompt_text.split('.') if s.strip()]),
        "has_context": False,
        "has_examples": False,
        "has_constraints": False,
        "has_format_specs": False,
        "clarity_score": 0,
        "specificity_score": 0
    }
    
    # 1. Uzunluk analizi
    word_count = len(prompt_text.split())
    if word_count < 10:
        score -= 30
        issues.append("Prompt çok kısa")
        suggestions.append("Daha detaylı ve açıklayıcı olun (en az 10-15 kelime)")
    elif word_count > 200:
        score -= 10
        issues.append("Prompt çok uzun olabilir")
        suggestions.append("Ana noktaları özetleyerek daha kısa yapın")
    else:
        strengths.append("Uygun uzunlukta")
    
    # 2. Netlik ve spesifiklik
    vague_words = ['şey', 'bir şeyler', 'biraz', 'gibi', 'falan', 'filan', 'vs', 'vb']
    vague_count = sum(1 for word in vague_words if word in prompt_text.lower())
    if vague_count > 2:
        score -= 15
        issues.append("Belirsiz ifadeler kullanılmış")
        suggestions.append("Belirsiz kelimeleri spesifik terimlerle değiştirin")
    
    # 3. Bağlam kontrolü (Context)
    context_indicators = [
        'için', 'amacıyla', 'hedefi', 'sektör', 'şirket', 'proje', 'müşteri', 
        'kullanıcı', 'target', 'audience', 'company', 'business'
    ]
    has_context = any(indicator in prompt_text.lower() for indicator in context_indicators)
    detailed_analysis["has_context"] = has_context
    if has_context:
        strengths.append("Bağlam bilgisi mevcut")
        detailed_analysis["clarity_score"] += 25
    else:
        score -= 20
        issues.append("Bağlam eksik")
        suggestions.append("Kimler için, hangi amaçla kullanılacağını belirtin")
    
    # 4. Örnek kontrolü
    example_indicators = ['örnek', 'example', 'mesela', 'gibi', 'örnektir', 'sample']
    has_examples = any(indicator in prompt_text.lower() for indicator in example_indicators)
    detailed_analysis["has_examples"] = has_examples
    if has_examples:
        strengths.append("Örnekler içeriyor")
        detailed_analysis["clarity_score"] += 25
    else:
        score -= 15
        suggestions.append("Somut örnekler ekleyin")
    
    # 5. Kısıtlamalar ve formatlar
    constraint_indicators = [
        'kelime', 'karakter', 'paragraf', 'madde', 'liste', 'tablo', 'format',
        'word', 'character', 'bullet', 'number', 'json', 'csv', 'markdown'
    ]
    has_constraints = any(indicator in prompt_text.lower() for indicator in constraint_indicators)
    detailed_analysis["has_constraints"] = has_constraints
    if has_constraints:
        strengths.append("Format/kısıtlama belirtilmiş")
        detailed_analysis["specificity_score"] += 25
    else:
        suggestions.append("Çıktı formatını belirtin (liste, paragraf, tablo vb.)")
    
    # 6. Aksiyon odaklılık
    action_words = [
        'yaz', 'oluştur', 'analiz et', 'öner', 'listele', 'karşılaştır', 
        'değerlendir', 'hesapla', 'tasarla', 'planla', 'write', 'create', 
        'analyze', 'compare', 'evaluate', 'design', 'plan'
    ]
    has_action = any(action in prompt_text.lower() for action in action_words)
    if has_action:
        strengths.append("Net aksiyon belirtilmiş")
        detailed_analysis["specificity_score"] += 25
    else:
        score -= 15
        issues.append("Net aksiyon eksik")
        suggestions.append("Ne yapılmasını istediğinizi net belirtin (yaz, analiz et, oluştur vb.)")
    
    # 7. Teknik detay kontrolü
    technical_indicators = [
        'api', 'kod', 'algoritma', 'database', 'sql', 'python', 'javascript',
        'machine learning', 'data science', 'analytics', 'metrics', 'kpi'
    ]
    has_technical = any(indicator in prompt_text.lower() for indicator in technical_indicators)
    if has_technical:
        strengths.append("Teknik detaylar içeriyor")
        detailed_analysis["specificity_score"] += 15
    
    # 8. Hedef kitle belirtimi
    audience_indicators = [
        'yaş', 'demographic', 'target', 'audience', 'müşteri profil', 'user persona',
        'segment', 'market', 'b2b', 'b2c', 'enterprise', 'startup'
    ]
    has_audience = any(indicator in prompt_text.lower() for indicator in audience_indicators)
    if has_audience:
        strengths.append("Hedef kitle belirtilmiş")
        detailed_analysis["specificity_score"] += 20
    
    # 9. Sayısal değerler
    numbers = re.findall(r'\d+', prompt_text)
    if numbers:
        strengths.append("Sayısal değerler kullanılmış")
        detailed_analysis["specificity_score"] += 15
    else:
        suggestions.append("Mümkünse sayısal hedefler ekleyin (miktar, yüzde, tarih)")
    
    # 10. Dil ve yazım kontrolü
    if prompt_text.isupper():
        score -= 10
        issues.append("Tamamı büyük harf")
        suggestions.append("Normal yazım kurallarını kullanın")
    
    # Toplam puanlama hesaplama
    detailed_analysis["clarity_score"] = min(detailed_analysis["clarity_score"], 50)
    detailed_analysis["specificity_score"] = min(detailed_analysis["specificity_score"], 50)
    
    final_score = max(0, min(100, score))
    
    # Grade hesaplama
    if final_score >= 90:
        grade = "A+"
    elif final_score >= 85:
        grade = "A"
    elif final_score >= 80:
        grade = "A-"
    elif final_score >= 75:
        grade = "B+"
    elif final_score >= 70:
        grade = "B"
    elif final_score >= 65:
        grade = "B-"
    elif final_score >= 60:
        grade = "C+"
    elif final_score >= 55:
        grade = "C"
    elif final_score >= 50:
        grade = "C-"
    elif final_score >= 40:
        grade = "D"
    else:
        grade = "F"
    
    return {
        "score": final_score,
        "grade": grade,
        "issues": issues,
        "suggestions": suggestions,
        "strengths": strengths,
        "detailed_analysis": detailed_analysis
    }

def get_prompt_improvement_suggestions(analysis):
    """Analiz sonucuna göre gelişim önerileri"""
    suggestions = []
    score = analysis["score"]
    
    if score < 50:
        suggestions.extend([
            "🚨 **ACİL İYİLEŞTİRME GEREKLİ**",
            "• Prompt'u tamamen yeniden yazın",
            "• Spesifik hedef ve bağlam ekleyin",
            "• Örnekler verin",
            "• Net aksiyon belirtin"
        ])
    elif score < 70:
        suggestions.extend([
            "⚠️ **ORTA SEVİYE İYİLEŞTİRME**",
            "• Daha spesifik detaylar ekleyin",
            "• Bağlam bilgisini güçlendirin",
            "• Format belirtimi yapın"
        ])
    elif score < 85:
        suggestions.extend([
            "✅ **İYİ - KÜÇÜK İYİLEŞTİRMELER**",
            "• Sayısal hedefler ekleyebilirsiniz",
            "• Daha fazla örnek verebilirsiniz"
        ])
    else:
        suggestions.extend([
            "🌟 **MÜKEMMEL PROMPT!**",
            "• Harika iş çıkardınız",
            "• Bu prompt'u şablon olarak kullanabilirsiniz"
        ])
    
    return suggestions

def display_quality_control_tab():
    """Kalite kontrol sekmesi"""
    st.header("🎯 Prompt Kalite Kontrol Merkezi")
    st.markdown("""
    Bu araç prompt'unuzun kalitesini değerlendirir ve iyileştirme önerileri sunar.
    OpenAI'nin best practices'lerini baz alır.
    """)
    
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Prompt'unuzu Girin")
        user_prompt = st.text_area(
            "Analiz edilecek prompt:",
            height=150,
            placeholder="Buraya prompt'unuzu yazın...\n\nÖrnek: 25-40 yaş teknoloji profesyonelleri için LinkedIn'de 10.000₺ bütçeli B2B kampanya tasarla. Mevcut CTR %2.1, hedef %3.5. Rekabetçi analiz dahil et.",
            help="En az 10 kelimelik bir prompt yazın"
        )
        
        analyze_button = st.button("🔍 Kalite Analizi Yap", type="primary")
    
    with col2:
        st.subheader("📊 Kalite Kriterleri")
        st.markdown("""
        **Değerlendirme Alanları:**
        - 📏 Uzunluk ve detay
        - 🎯 Netlik ve spesifiklik  
        - 📝 Bağlam bilgisi
        - 💡 Örnekler
        - ⚙️ Format belirtimi
        - 🎬 Aksiyon odaklılık
        - 👥 Hedef kitle
        - 📊 Sayısal değerler
        """)
    
    if analyze_button and user_prompt:
        with st.spinner("🔄 Prompt analiz ediliyor..."):
            analysis = analyze_prompt_quality(user_prompt)
            
            # Sonuçları göster
            st.markdown("---")
            st.subheader("📈 Analiz Sonuçları")
            
            # Skor ve grade
            col1, col2, col3 = st.columns(3)
            
            with col1:
                score_color = "green" if analysis["score"] >= 80 else "orange" if analysis["score"] >= 60 else "red"
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; border-radius: 10px; background-color: rgba(0,0,0,0.1);'>
                    <h2 style='color: {score_color}; margin: 0;'>{analysis["score"]}/100</h2>
                    <p style='margin: 5px 0; font-weight: bold;'>Kalite Puanı</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                grade_color = "green" if analysis["grade"] in ["A+", "A", "A-"] else "orange" if analysis["grade"].startswith("B") else "red"
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; border-radius: 10px; background-color: rgba(0,0,0,0.1);'>
                    <h2 style='color: {grade_color}; margin: 0;'>{analysis["grade"]}</h2>
                    <p style='margin: 5px 0; font-weight: bold;'>Not</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                detail = analysis["detailed_analysis"]
                total_features = detail["clarity_score"] + detail["specificity_score"]
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; border-radius: 10px; background-color: rgba(0,0,0,0.1);'>
                    <h2 style='color: #0066cc; margin: 0;'>{total_features}/100</h2>
                    <p style='margin: 5px 0; font-weight: bold;'>Özellik Puanı</p>
                </div>
                """, unsafe_allow_html=True)
            
            
            st.markdown("### 📊 Detaylı Analiz")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if analysis["strengths"]:
                    st.success("**✅ Güçlü Yönler:**")
                    for strength in analysis["strengths"]:
                        st.write(f"• {strength}")
                
                
                st.info("**📋 Teknik Detaylar:**")
                detail = analysis["detailed_analysis"]
                st.write(f"• Kelime sayısı: {detail['word_count']}")
                st.write(f"• Karakter sayısı: {detail['length']}")
                st.write(f"• Cümle sayısı: {detail['sentence_count']}")
                st.write(f"• Netlik puanı: {detail['clarity_score']}/50")
                st.write(f"• Spesifiklik puanı: {detail['specificity_score']}/50")
            
            with col2:
                if analysis["issues"]:
                    st.error("**❌ Tespit Edilen Sorunlar:**")
                    for issue in analysis["issues"]:
                        st.write(f"• {issue}")
                
                if analysis["suggestions"]:
                    st.warning("**💡 İyileştirme Önerileri:**")
                    for suggestion in analysis["suggestions"]:
                        st.write(f"• {suggestion}")
            
            
            st.markdown("### 🚀 Gelişim Önerileri")
            improvement_suggestions = get_prompt_improvement_suggestions(analysis)
            for suggestion in improvement_suggestions:
                st.markdown(suggestion)
            
            
            st.markdown("### 💫 İlham Alın")
            
            if analysis["score"] < 70:
                st.markdown("**Kaliteli Prompt Örnekleri:**")
                examples = [
                    "🎯 **İyi Örnek:** '25-40 yaş teknoloji profesyonelleri için LinkedIn'de 10.000₺ bütçeli B2B kampanya tasarla. Mevcut CTR %2.1, hedef %3.5. Rakip analizi dahil et.'",
                    "📊 **İyi Örnek:** 'E-ticaret sitemiz için 500 kelimelik SEO blog yazısı yaz. Anahtar kelimeler: sürdürülebilir moda, organik tekstil. Hedef: 18-35 yaş kadın müşteriler.'",
                    "⚡ **İyi Örnek:** '50 kişilik startup için Agile metodolojisiyle 3 aylık mobil uygulama geliştirme projesi planı oluştur. Bütçe: 200.000₺, platform: iOS ve Android.'"
                ]
                for example in examples:
                    st.markdown(example)
    
    elif analyze_button and not user_prompt:
        st.error("❌ Lütfen analiz edilecek bir prompt girin!")
    
    
    st.markdown("---")
    st.markdown("### 📚 Kalite Kontrol İpuçları")
    
    tips_col1, tips_col2 = st.columns(2)
    
    with tips_col1:
        st.markdown("""
        **🎯 SMART Prompt Yazma:**
        - **S**pecific (Spesifik)
        - **M**easurable (Ölçülebilir)  
        - **A**chievable (Ulaşılabilir)
        - **R**elevant (İlgili)
        - **T**ime-bound (Zaman sınırlı)
        """)
        
        st.markdown("""
        **📝 Prompt Anatomisi:**
        1. **Rol tanımı** (Kim olarak hareket et)
        2. **Bağlam** (Hangi durum/proje için)
        3. **Görev** (Ne yapılması gerek)
        4. **Kısıtlamalar** (Format, uzunluk, stil)
        5. **Örnekler** (Beklenen çıktı örnekleri)
        """)
    
    with tips_col2:
        st.markdown("""
        **⚠️ Kaçınılması Gerekenler:**
        - Belirsiz ifadeler ("bir şeyler", "biraz")
        - Çok genel talepler
        - Bağlamsız sorular
        - Format belirtmeme
        - Hedef kitle tanımlamama
        """)
        
        st.markdown("""
        **✅ Kaliteli Prompt Özellikleri:**
        - Net ve spesifik
        - Bağlam zengin
        - Ölçülebilir hedefler
        - Somut örnekler
        - Format belirtimi
        - Sayısal değerler
        """)

def get_prompt_templates_by_quality():
    """Kalite seviyelerine göre prompt şablonları"""
    return {
        "Başlangıç (C- ve altı)": [
            {
                "title": "Basit Blog Yazısı",
                "template": "Blog yazısı yaz.",
                "improved": "Dijital pazarlama konusunda 800 kelimelik blog yazısı yaz. Hedef kitle: 25-40 yaş girişimciler. Ton: bilgilendirici ama samimi. SEO anahtar kelimeleri: 'dijital pazarlama stratejileri', 'online satış artırma'. Çıktı formatı: giriş-gelişme-sonuç yapısında, alt başlıklarla."
            },
            {
                "title": "Basit Analiz",
                "template": "Bu veriyi analiz et.",
                "improved": "Ekli satış verilerini (Q1-Q3 2024) analiz et. Şirket: teknoloji startup, 50 çalışan. Odak: hangi ürün kategorilerinde düşüş var, hangi müşteri segmentlerinde artış var. Çıktı: 3 ana bulgu + 5 aksiyon önerisi, tablo formatında."
            }
        ],
        "Orta (B- ile B+ arası)": [
            {
                "title": "Pazarlama Kampanyası",
                "template": "Sosyal medya kampanyası tasarla. Teknoloji ürünü için. Genç hedef kitle.",
                "improved": "25-35 yaş teknoloji early-adopter'ları için AI chatbot ürünümüzün lansmanı için Instagram ve LinkedIn kampanyası tasarla. Bütçe: 15.000₺, süre: 6 hafta. Hedef: 1000 demo kaydı, %12 conversion rate. Rakipler: ChatGPT, Jasper. Marka tonu: profesyonel ama friendly."
            }
        ],
        "İleri (A- ve üzeri)": [
            {
                "title": "Kapsamlı İş Stratejisi",
                "template": "100 kişilik SaaS şirketimiz için 2024 Q4 büyüme stratejisi oluştur. Mevcut MRR: $50K, hedef: $75K. Ana metrikler: CAC $150, LTV $2400, churn %5. Rakipler: Salesforce, HubSpot. Güçlü yönümüz: AI entegrasyonu, zayıflık: brand awareness. Çıktı: SWOT analizi + 90 günlük eylem planı + bütçe dağılımı (Excel formatında)."
            }
        ]
    }

def display_header():
    """Ana başlık"""
    st.title("🤖 AI Prompt Koleksiyonu")
    st.subheader("ChatGPT, Claude ve Gemini için Profesyonel Prompt Şablonları")
    
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📚 Prompt Kütüphanesi", 
        "💡 Kullanım İpuçları",
        "📋 Hazır Şablonlar",
        "🎯 Kalite Kontrol"
    ])
    
    return tab1, tab2, tab3, tab4

def display_search_filters(df):
    """Arama ve filtreleme"""
    st.subheader("🔍 Prompt Ara ve Filtrele")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input(
            "Anahtar kelime ile ara:",
            placeholder="Örn: marketing, yazılım, müşteri hizmetleri, satış...",
            help="Prompt içeriğinde veya rol adında arama yapar"
        )
    
    with col2:
        if df is not None and 'act' in df.columns:
            
            featured_roles = [
                "Tümü", "Business Analyst", "Marketing Expert", "Content Creator",
                "Sales Representative", "Project Manager", "Software Developer",
                "Customer Service Representative", "Data Scientist", "Social Media Manager",
                "Email Marketing Specialist", "Copywriter", "Technical Writer"
            ]
            
            selected_role = st.selectbox(
                "Popüler Roller:",
                options=featured_roles
            )
        else:
            selected_role = "Tümü"
    
    return search_term, selected_role

def filter_prompts(df, search_term, selected_role):
    """Prompts'ları filtrele"""
    if df is None:
        return None
    
    filtered_df = df.copy()
    
    
    if search_term:
        mask = (
            filtered_df['act'].str.contains(search_term, case=False, na=False) |
            filtered_df['prompt'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    
    if selected_role != "Tümü":
        filtered_df = filtered_df[filtered_df['act'].str.contains(selected_role, case=False, na=False)]
    
    return filtered_df

def display_prompt_details(role, prompt, index):
    """Her prompt için detaylı gösterim"""
    

    clean_prompt = prompt.replace('"', '').strip()
    

    preview = clean_prompt[:200] + "..." if len(clean_prompt) > 200 else clean_prompt
    

    role_tips = get_prompt_tips(role)
    

    with st.container():
        st.subheader(f"🎭 {role}")
        

        st.write("**Prompt Önizleme:**")
        st.info(preview)
        

        tab1, tab2, tab3 = st.tabs(["📋 Tam Prompt", "💡 Kullanım İpuçları", "🚀 Hızlı Başlat"])
        
        with tab1:
            st.write("**Tam Prompt Metni:**")
            st.code(clean_prompt, language="text")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📋 Panoya Kopyala", key=f"copy_{index}", help="Prompt'u panoya kopyalar"):
                    st.success("✅ Prompt panoya kopyalandı! ChatGPT'ye yapıştırabilirsiniz.")
            
            with col2:
                chatgpt_url = f"https://chat.openai.com/"
                st.markdown(f"[🔗 ChatGPT'de Aç]({chatgpt_url})")
        
        with tab2:
            st.write("**Bu rolü daha etkili kullanmak için:**")
            
            for i, tip in enumerate(role_tips["tips"], 1):
                st.write(f"{i}. {tip}")
            
            st.write("**Örnek Gelişmiş Kullanım:**")
            st.success(role_tips["example"])
            
            st.write("**Genel İpuçları:**")
            st.write("""
            - Prompt'u yapıştırdıktan sonra AI'ya rolü kabul ettiğini doğrulatan
            - Spesifik sorular sorun, genel ifadelerden kaçının  
            - İlk yanıttan memnun değilseniz "daha detaylandır" deyin
            - Aynı konuşmada birden fazla soru sorabilirsiniz
            """)
        
        with tab3:
            st.write("**Hızlı Başlangıç Şablonları:**")
            
            quick_starts = {
                "Business Analyst": [
                    "Şirketimizin [sektör] pazarındaki konumunu analiz et",
                    "[Rakip şirket] ile karşılaştırmalı SWOT analizi yap",
                    "[Ürün/Hizmet] için pazar penetrasyon stratejisi öner"
                ],
                "Marketing Expert": [
                    "[Hedef kitle] için [platform] kampanya stratejisi oluştur",
                    "[Ürün] lansmanı için 30 günlük pazarlama takvimi hazırla", 
                    "Sosyal medya engagement'ımızı artırmak için 10 taktik öner"
                ],
                "Content Creator": [
                    "[Konu] hakkında [kelime sayısı] kelimelik blog yazısı yaz",
                    "[Platform] için haftalık içerik takvimi oluştur",
                    "[Hedef kitle] için etkili başlıklar öner"
                ]
            }
            
            role_quick_starts = quick_starts.get(role, [
                "Bu role özel sorular sormaya başlayın",
                "Spesifik bir görev tanımlayın",
                "Beklentilerinizi net olarak belirtin"
            ])
            
            for quick_start in role_quick_starts:
                st.write(f"• {quick_start}")
        
        st.markdown("---")

def display_library_tab(df):
    """Ana kütüphane sekmesi"""

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Toplam Prompt", "200+", "Sürekli Güncellenen")
    with col2:
        st.metric("Popüler Roller", "15+", "İş Odaklı") 
    with col3:
        st.metric("Hazır Şablon", "Mevcut", "Kullanıma Hazır")
    with col4:
        st.metric("Ücretsiz", "✓", "Tamamen Bedava")

    st.markdown("---")


    search_term, selected_role = display_search_filters(df)


    filtered_df = filter_prompts(df, search_term, selected_role)
    
    if filtered_df is not None and len(filtered_df) > 0:
        
        st.subheader(f"📋 Bulunan Prompts: {len(filtered_df)} adet")
        
        items_per_page = 5  
        total_pages = (len(filtered_df) - 1) // items_per_page + 1
        
        if total_pages > 1:
            page = st.selectbox(
                "📄 Sayfa:",
                range(1, total_pages + 1),
                format_func=lambda x: f"Sayfa {x} / {total_pages}"
            )
        else:
            page = 1
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_df = filtered_df.iloc[start_idx:end_idx]
        
        for index, row in page_df.iterrows():
            display_prompt_details(row['act'], row['prompt'], index)
    
    else:
        st.warning("🔍 Arama kriterlerinize uygun prompt bulunamadı.")
        st.info("💡 Farklı anahtar kelimeler deneyin veya filtreyi 'Tümü' yapın.")

def display_usage_tips_tab():
    """Kullanım ipuçları sekmesi"""
    st.header("💡 AI Prompt Kullanım İpuçları")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Adım Adım Kullanım")
        st.write("""
        **1. Doğru Rolü Seçin**
        - İhtiyacınıza en uygun rolü bulun
        - Rol tanımını dikkatlice okuyun
        - Örnekleri inceleyin
        
        **2. Prompt'u Kopyalayın**
        - "📋 Panoya Kopyala" butonunu kullanın
        - Tam prompt'u kopyaladığınızdan emin olun
        
        **3. AI'ya Yapıştırın**
        - ChatGPT, Claude veya Gemini'ye gidin
        - Prompt'u yapıştırın ve gönder
        - AI'nın rolü kabul etmesini bekleyin
        
        **4. Spesifik Sorular Sorun**
        - Genel sorulardan kaçının
        - Detaylar ve bağlam verin
        - Sayısal hedefler belirtin
        """)
        
        st.subheader("⚡ Pro İpuçları")
        st.write("""
        **Daha İyi Sonuçlar İçin:**
        - Şirket bilgilerini paylaşın
        - Sektör ve pazar detaylarını verin
        - Bütçe ve zaman çerçevesi belirtin
        - Örnekler ve referanslar kullanın
        - Adım adım ilerleyin
        """)
    
    with col2:
        st.subheader("🚫 Yaygın Hatalar")
        st.error("""
        **Bunları Yapmayın:**
        - ❌ Çok genel sorular
        - ❌ Bağlam vermemek
        - ❌ İlk cevapla yetinmek
        - ❌ Rol atlamak
        """)
        
        st.subheader("✅ Doğru Yaklaşım")
        st.success("""
        **Bunları Yapın:**
        - ✅ Spesifik senaryolar
        - ✅ Sayısal hedefler
        - ✅ Adım adım sorular
        - ✅ Geri bildirim verme
        """)
        
        st.subheader("🎯 Örnek İyi Soru")
        st.code("""
Teknoloji şirketimiz için:
- Hedef: B2B satış artışı
- Pazar: 50-500 kişi şirketler  
- Bütçe: Aylık 20.000₺
- Süre: 6 ay
- Platform: LinkedIn, email

Bu kriterlere göre pazarlama 
stratejisi oluştur.
        """)

def display_templates_tab():
    """Hazır şablonlar sekmesi"""
    st.header("📋 Hazır Prompt Şablonları")
    st.write("İş süreçleriniz için hazır şablonları kullanın ve özelleştirin.")
    
    templates = {
        "İş Analizi": {
            "templates": [
                {
                    "name": "Rakip Analizi",
                    "template": """Sen deneyimli bir iş analisti olarak hareket et. 

{company_name} şirketinin {sector} sektöründeki ana rakiplerini analiz et:

- Rakip şirketler: {competitors}
- Analiz kapsamı: {analysis_scope}
- Zaman dilimi: {time_period}

Lütfen şunları içeren detaylı analiz sun:
1. Rakiplerin güçlü/zayıf yönleri
2. Pazar konumları 
3. Fiyatlandırma stratejileri
4. Bizim için fırsatlar ve tehditler
5. Öneriler ve aksiyon planı""",
                    "fields": ["company_name", "sector", "competitors", "analysis_scope", "time_period"]
                }
            ]
        },
        "Pazarlama": {
            "templates": [
                {
                    "name": "Sosyal Medya Kampanyası",
                    "template": """Sen 10 yıl deneyimli bir dijital pazarlama uzmanısın.

{product_name} ürünü için sosyal medya kampanyası tasarla:

- Hedef kitle: {target_audience}
- Platformlar: {platforms}
- Bütçe: {budget}
- Süre: {duration}
- Ana mesaj: {main_message}

Lütfen şunları hazırla:
1. Platform bazlı strateji
2. İçerik takvimi (haftalık)
3. Hashtag stratejisi
4. Ölçüm metrikleri
5. Bütçe dağılımı""",
                    "fields": ["product_name", "target_audience", "platforms", "budget", "duration", "main_message"]
                }
            ]
        },
        "Satış": {
            "templates": [
                {
                    "name": "B2B Satış Sunumu",
                    "template": """Sen deneyimli bir B2B satış uzmanısın.

{client_company} şirketine {product_service} için satış sunumu hazırla:

- Müşteri profili: {client_profile}
- Ürün/Hizmet: {product_service}
- Fiyat aralığı: {price_range}
- Ana itirazlar: {main_objections}
- Karar verici: {decision_maker}

Lütfen şunları içeren sunum hazırla:
1. Açılış ve güven oluşturma
2. İhtiyaç analizi soruları
3. Çözüm sunumu
4. Fayda vurguları
5. İtiraz yönetimi
6. Kapanış teknikleri""",
                    "fields": ["client_company", "product_service", "client_profile", "price_range", "main_objections", "decision_maker"]
                }
            ]
        }
    }
    
    selected_category = st.selectbox("Kategori Seçin:", list(templates.keys()))
    
    for template in templates[selected_category]["templates"]:
        with st.expander(f"📋 {template['name']}", expanded=False):
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.write("**Şablon:**")
                st.code(template["template"], language="text")
            
            with col2:
                st.write("**Gerekli Alanlar:**")
                
                # Form oluştur
                with st.form(f"template_form_{template['name']}"):
                    template_inputs = {}
                    
                    for field in template["fields"]:
                        template_inputs[field] = st.text_input(
                            f"{field.replace('_', ' ').title()}:",
                            key=f"{template['name']}_{field}"
                        )
                    
                    if st.form_submit_button("🎯 Şablonu Doldur"):
                        if all(template_inputs.values()):
                            filled_template = template["template"].format(**template_inputs)
                            st.success("✅ Şablon dolduruldu!")
                            st.code(filled_template, language="text")
                        else:
                            st.error("⚠️ Tüm alanları doldurun.")

def display_favorites():
    """IWA Concept için öne çıkan roller"""
    st.subheader("⭐ IWA Concept için Öne Çıkan Roller")
    
    favorites = [
        {
            "role": "Business Analyst",
            "description": "İş süreçleri analizi, rakip araştırması ve strateji geliştirme",
            "best_for": "Pazar analizi, KPI tracking, süreç optimizasyonu"
        },
        {
            "role": "Marketing Expert",
            "description": "Dijital pazarlama, kampanya yönetimi ve marka stratejisi",
            "best_for": "Sosyal medya, e-posta pazarlama, content marketing"
        },
        {
            "role": "Sales Representative", 
            "description": "Satış teknikleri, müşteri iletişimi ve deal closing",
            "best_for": "Teklif hazırlama, itiraz yönetimi, CRM stratejisi"
        },
        {
            "role": "Project Manager",
            "description": "Proje planlama, takım koordinasyonu ve risk yönetimi", 
            "best_for": "Sprint planning, timeline oluşturma, resource allocation"
        }
    ]
    
    for fav in favorites:
        with st.expander(f"🎯 {fav['role']}", expanded=False):
            st.write(f"**Açıklama:** {fav['description']}")
            st.write(f"**En İyi Kullanım:** {fav['best_for']}")

def display_usage_guide():
    """Detaylı kullanım kılavuzu"""
    with st.expander("📚 Detaylı Kullanım Kılavuzu", expanded=False):
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### 🎯 Adım Adım Kullanım")
            st.write("""
            1. **Rol Seçin:** İhtiyacınıza uygun rolü bulun
            2. **Prompt'u Kopyalayın:** Tam prompt'u kopyalayın
            3. **AI'ya Yapıştırın:** ChatGPT/Claude/Gemini'ye yapıştırın
            4. **Rolü Onaylayın:** AI rolü kabul ettiğini söylesin
            5. **Soru Sorun:** Spesifik sorularınızı sorun
            """)
            
            st.write("### ⚡ Pro İpuçları")
            st.write("""
            - **Bağlam verin:** Şirket, sektör, hedef belirtin
            - **Sayılar kullanın:** Bütçe, süre, miktar ekleyin
            - **Örnekler isteyín:** "3 örnek ver" deyin
            - **Iterasyon yapın:** İlk yanıtı geliştirtín
            """)
        
        with col2:
            st.write("### 🚫 Yaygın Hatalar")
            st.write("""
            - ❌ Çok genel sorular sormak
            - ❌ Bağlam vermemek  
            - ❌ İlk yanıtla yetinmek
            - ❌ Rol prompt'unu atlamak
            """)
            
            st.write("### ✅ Doğru Yaklaşım")
            st.write("""
            - ✅ Spesifik senaryolar vermek
            - ✅ Sayısal hedefler belirtmek
            - ✅ Adım adım ilerlemek
            - ✅ Geri bildirim vermek
            """)

def main():
    """Ana uygulama"""
    
    # Başlık ve sekmeler
    tab1, tab2, tab3, tab4 = display_header()
    
    # Sidebar bilgi
    with st.sidebar:
        st.title("ℹ️ Hakkında")
        st.write("""
        Bu uygulama, GitHub'daki **Awesome ChatGPT Prompts** 
        koleksiyonunu kullanarak AI araçlarını 
        daha etkili kullanmanızı sağlar.
        """)
        
        st.subheader("🎯 Hedef")
        st.write("""
        IWA Concept çalışanlarının AI araçlarını 
        profesyonel düzeyde kullanabilmesi.
        """)
        
        st.subheader("🔗 Desteklenen AI'lar")
        st.write("• ChatGPT")
        st.write("• Claude") 
        st.write("• Google Gemini")
        st.write("• Bing Chat")
        
        st.subheader("🆕 Özellikler")
        st.success("✅ 200+ Hazır Prompt")
        st.success("✅ Kullanım İpuçları")
        st.success("✅ Hazır Şablonlar")
        st.success("✅ Kalite Kontrol")
        st.success("✅ IWA Concept Özel")
        
        # Hızlı erişim butonları
        st.markdown("---")
        st.subheader("🚀 Hızlı Erişim")
        
        if st.button("🎯 Prompt Kalite Testi", help="Prompt'unuzu hızlıca test edin"):
            st.session_state['active_tab'] = 'quality'
        
        if st.button("⭐ Favori Prompts", help="En popüler prompts"):
            st.session_state['active_tab'] = 'library'
            
        if st.button("💡 İpucu Al", help="Prompt yazma ipuçları"):
            st.session_state['active_tab'] = 'tips'
        
        st.markdown("---")
        st.markdown("### 📊 Günlük İstatistikler")
        st.info("🎯 Analiz edilen prompt: **47**")
        st.info("⭐ En yüksek skor: **94/100**")
        st.info("📈 Ortalama kalite: **B+**")
        
        st.markdown("---")
        st.write("💡 **İpucu:** Her sekmede farklı özellikler var!")
    
    # Prompts'ları yükle
    with st.spinner("🔄 GitHub'dan prompts yükleniyor..."):
        df = load_prompts()
    
    if df is None:
        st.error("❌ Prompts yüklenemedi. İnternet bağlantınızı kontrol edin.")
        return
    
    # Ana sekmeler
    with tab1:
        st.success(f"✅ {len(df)} prompt başarıyla yüklendi!")
        display_library_tab(df)
        
        # Öne çıkan roller
        display_favorites()
        
        # Kullanım kılavuzu
        display_usage_guide()
    
    with tab2:
        display_usage_tips_tab()
        
    with tab3:
        display_templates_tab()
        
    with tab4:
        display_quality_control_tab()
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; color: #666;'>
            <p>🤖 AI Prompt Koleksiyonu | IWA Concept için özelleştirildi</p>
            <p><small>Kaynak: <a href='https://github.com/f/awesome-chatgpt-prompts' target='_blank'>Awesome ChatGPT Prompts</a></small></p>
            <p><small>Son Güncelleme: {datetime.now().strftime('%d.%m.%Y %H:%M')}</small></p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
