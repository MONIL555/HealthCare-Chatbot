import json
import random

QA_PAIRS = [
    {
        "base_problem": "severe body pain and muscle ache",
        "answers": [
            "Severe body and muscle pain can be caused by viral infections (like the flu), extreme physical exertion, or stress. Drink plenty of water, rest, and consider an over-the-counter pain reliever like ibuprofen. If the pain is accompanied by a high fever or lasts more than a few days, please see a doctor.",
            "Muscle aches and widespread body pain often signal a viral illness, dehydration, or pushing yourself too hard physically. Take time to rest, hydrate well, and try an NSAID for relief. Seek medical care if the pain persists or is joined by a high fever.",
            "When your whole body hurts, it's usually your immune system fighting off a bug, or simply exhaustion. Rest up, drink plenty of fluids, and use a warm compress or ibuprofen to ease the soreness. Consult a physician if symptoms worsen or drag on for days."
        ],
        "keywords": ["body pain", "muscle ache", "muscles hurt", "body ache", "whole body hurts", "sore muscles"]
    },
    {
        "base_problem": "high fever",
        "answers": [
            "A high fever is your body's way of fighting off an infection. Rest, drink plenty of fluids to prevent dehydration, and consider taking acetaminophen or ibuprofen to lower your temperature. If the fever exceeds 103°F (39.4°C), lasts longer than 3 days, or is accompanied by a severe headache or stiff neck, seek medical attention immediately.",
            "Running a high temperature usually means you have an infection. It's crucial to stay hydrated and get plenty of rest. You can use fever reducers like ibuprofen. However, if it spikes over 103°F or doesn't break after a few days, please go to a doctor.",
            "Fevers help your body fight illness. Drink water constantly, stay cool, and try acetaminophen if you're uncomfortable. Watch out for danger signs: a temperature above 103°F, a stiff neck, or extreme lethargy require immediate emergency care."
        ],
        "keywords": ["fever", "high temperature", "running a fever", "burning up", "hot to touch", "feverish"]
    },
    {
        "base_problem": "persistent cough",
        "answers": [
            "A persistent cough could be a sign of a respiratory infection, allergies, or asthma. Drink warm fluids like tea with honey, use a humidifier, and try over-the-counter cough suppressants. If you are coughing up blood, experiencing chest pain, or the cough lasts more than 3 weeks, consult a pulmonologist.",
            "Coughing that won't go away is often due to lingering respiratory viruses, post-nasal drip, or asthma. Soothe your throat with honey and warm tea, and run a humidifier at night. See a doctor if you cough up blood, have chest pain, or if it lasts weeks.",
            "When a cough hangs on, it irritates your throat and disrupts sleep. Try over-the-counter suppressants, stay hydrated, and use throat lozenges. It is important to get checked by a doctor if you feel shortness of breath, chest pain, or if it persists beyond 3 weeks."
        ],
        "keywords": ["cough", "coughing a lot", "persistent cough", "can't stop coughing", "dry cough", "wet cough"]
    },
    {
        "base_problem": "hair fall and thinning",
        "answers": [
            "Hair fall and thinning can be triggered by stress, nutritional deficiencies, genetics, or hormonal imbalances. Use gentle hair care products, eat a diet rich in protein and vitamins (especially Biotin and Iron), and avoid excessive heat styling. If the hair loss is sudden, patchy, or severe, consult a dermatologist.",
            "Losing hair is often tied to stress, diet, or hormones. Make sure you are eating enough protein and iron, and treat your hair gently by avoiding tight hairstyles and heat. A dermatologist can help if the shedding is sudden or leaves bald patches.",
            "Noticeable hair thinning can be alarming, but it's frequently caused by reversible factors like stress or vitamin deficiencies. Focus on a balanced diet and gentle scalp care. If you see sudden clumps falling out, schedule a visit with a skin and hair specialist."
        ],
        "keywords": ["hair fall", "hair thinning", "losing hair", "bald patches", "hair dropping", "shedding hair"]
    },
    {
        "base_problem": "stomach ache and nausea",
        "answers": [
            "Stomach aches and nausea are common symptoms of food poisoning, gastroenteritis, or indigestion. Sip clear fluids like water or ginger ale, stick to the BRAT diet (Bananas, Rice, Applesauce, Toast), and avoid dairy or greasy foods. If you experience severe abdominal pain, vomiting blood, or cannot keep liquids down for 24 hours, go to the emergency room.",
            "Feeling nauseous with stomach cramps usually points to a stomach bug or something you ate. Rest your stomach by sticking to clear liquids and plain foods like crackers or toast. Seek urgent care if you have unbearable pain, vomit blood, or become severely dehydrated.",
            "An upset stomach can be very uncomfortable. Stay hydrated by taking small sips of water or electrolyte drinks, and avoid heavy, spicy, or dairy-rich foods. If the pain is sharp and localized, or if you can't keep any fluids down, you need a medical evaluation."
        ],
        "keywords": ["stomach ache", "nausea", "feel sick", "tummy hurts", "vomiting", "throwing up", "upset stomach"]
    },
    {
        "base_problem": "minor burn",
        "answers": [
            "For a minor burn, immediately cool the area under running water (not freezing cold) for 10-15 minutes. Apply aloe vera or a soothing moisturizer and cover with a sterile, non-adhesive bandage. Do not pop any blisters. If the burn is larger than 3 inches, on your face, or extremely deep, seek urgent medical care.",
            "Treat small burns by running cool water over the area for about 15 minutes. Once cooled, apply an aloe vera gel and wrap it loosely with a clean bandage. Never pop blisters. If the burn looks charred, is very large, or is on your face or joints, go to the ER.",
            "If you've suffered a minor burn, cool it down quickly with cool tap water. Protect the skin with a sterile dressing and use aloe to soothe it. Do not use ice directly. Seek immediate medical attention for deep burns, electrical burns, or large affected areas."
        ],
        "keywords": ["burned my", "burn", "scalded", "hot water burn", "touch hot"]
    },
    {
        "base_problem": "sprained ankle",
        "answers": [
            "For a suspected sprained ankle, follow the R.I.C.E protocol: Rest the ankle, Ice it for 20 minutes every few hours, Compress with an elastic bandage, and Elevate it above your heart. Take over-the-counter anti-inflammatories for pain. If you cannot bear any weight on it, see an orthopedist to rule out a fracture.",
            "A twisted ankle needs the RICE method: Rest, Ice, Compression, and Elevation. Keep weight off the foot and use ibuprofen to manage swelling. If the pain is extreme, or you physically cannot stand on it, get an X-ray to ensure it isn't broken.",
            "If you've rolled your ankle, stop putting weight on it. Wrap it for compression, prop it up on pillows, and apply ice packs periodically. If swelling is severe or you can't walk at all, have a doctor examine it for torn ligaments or fractures."
        ],
        "keywords": ["sprained ankle", "twisted ankle", "rolled ankle", "ankle hurts", "swollen ankle"]
    },
    {
        "base_problem": "skin rash",
        "answers": [
            "A skin rash can result from allergies, contact dermatitis, or infections. Wash the area gently with mild soap and water, apply a cool compress, and use an over-the-counter hydrocortisone cream to reduce itching. Avoid scratching to prevent infection. If the rash spreads rapidly, is very painful, or is accompanied by a fever, see a doctor.",
            "Rashes are often allergic reactions or irritation. Keep the skin clean, avoid hot showers, and apply anti-itch creams like hydrocortisone or calamine lotion. If the rash starts blistering, spreading quickly, or occurs alongside a fever, it warrants a doctor's visit.",
            "If you have an itchy rash, try not to scratch it. Use cool compresses and over-the-counter allergy meds or creams to soothe the skin. Medical attention is necessary if the rash covers a large area of your body, looks infected, or causes difficulty breathing."
        ],
        "keywords": ["rash", "red spots", "itchy skin", "hives", "allergic reaction on skin"]
    },
    {
        "base_problem": "headache",
        "answers": [
            "Headaches can be caused by dehydration, stress, lack of sleep, or eye strain. Drink a large glass of water, rest in a quiet dark room, and take acetaminophen or ibuprofen if needed. If it's the \"worst headache of your life\", comes on suddenly, or is accompanied by vision changes or numbness, seek emergency care immediately.",
            "When dealing with a headache, the best first steps are to hydrate, step away from screens, and rest in a dim room. NSAIDs can help dull the pain. However, a sudden, extremely severe headache or one with neurological symptoms like weakness requires a 911 call.",
            "A pounding head is frequently linked to tension or dehydration. Try drinking plenty of fluids, massaging your temples, and resting. Take an over-the-counter pain reliever if necessary. Always go to the ER if the headache is sudden and explosively painful."
        ],
        "keywords": ["headache", "head hurts", "migraine", "pounding head", "throbbing head"]
    },
    {
        "base_problem": "sore throat",
        "answers": [
            "A sore throat is usually viral but can be bacterial (like strep throat). Gargle with warm salt water, drink warm liquids like tea with honey, and use throat lozenges to numb the pain. If you have white patches in the back of your throat, a high fever, or difficulty swallowing, consult a doctor for a potential antibiotic prescription.",
            "To soothe a scratchy throat, drink lots of warm fluids, use throat sprays, and gargle with salt water several times a day. Most are viral, but if you notice white spots on your tonsils or have a high fever, you should get swabbed for strep throat.",
            "Sore throats can be very painful but usually resolve with rest, hydration, and honey. Lozenges can help with the discomfort. See a healthcare provider if swallowing becomes nearly impossible, or if you run a high temperature, as you might need antibiotics."
        ],
        "keywords": ["sore throat", "throat hurts", "swallowing hurts", "scratchy throat"]
    },
    {
        "base_problem": "managing diabetes",
        "answers": [
            "Managing diabetes requires checking your blood sugar regularly, maintaining a balanced diet low in refined carbohydrates, exercising daily, and taking insulin or medications exactly as prescribed by your endocrinologist. Keep a log of your readings and see your doctor for regular A1C checks.",
            "To keep diabetes under control, consistency is key. Monitor your glucose levels, eat plenty of fiber and lean proteins, and stay physically active. Always adhere to your medication schedule and work closely with your medical team to track your long-term A1C.",
            "Living with diabetes means prioritizing a healthy lifestyle. Focus on complex carbs, avoid sugary drinks, check your blood sugar as advised, and take your prescribed treatments without skipping doses. Regular check-ups are essential to prevent complications."
        ],
        "keywords": ["diabetes", "high blood sugar", "type 2 diabetes", "manage blood sugar", "diabetic"]
    },
    {
        "base_problem": "high blood pressure",
        "answers": [
            "To help manage high blood pressure, reduce your sodium (salt) intake, engage in at least 30 minutes of aerobic exercise daily, manage stress through relaxation techniques, and limit alcohol consumption. Always take your prescribed antihypertensive medications and monitor your pressure at home.",
            "Hypertension requires lifestyle adjustments like cutting back on salty foods, exercising regularly, and managing stress. It is crucial to take your blood pressure medication exactly as your doctor instructed and to keep a log of your readings at home.",
            "Lowering high blood pressure is a mix of diet, exercise, and medication. Focus on a heart-healthy diet, try to walk or be active every day, and never stop taking your blood pressure pills without consulting your cardiologist first."
        ],
        "keywords": ["high blood pressure", "hypertension", "lower blood pressure", "BP is high"]
    },
    {
        "base_problem": "period cramps",
        "answers": [
            "For severe menstrual cramps, apply a heating pad to your lower abdomen, take NSAIDs like ibuprofen before the pain becomes severe, stay hydrated, and try gentle exercises like yoga. If the pain is debilitating or accompanied by extremely heavy bleeding, consult an OB-GYN to rule out conditions like endometriosis.",
            "Period pain can often be managed with a hot water bottle, resting, and over-the-counter pain relievers like naproxen or ibuprofen. Staying active with light stretching can also help. If the cramps regularly disrupt your daily life, speak to a gynecologist.",
            "To ease dysmenorrhea (cramps), use heat therapy on your stomach or back and take anti-inflammatory medication early in your cycle. Herbal teas like chamomile can also soothe cramps. Debilitating pain isn't normal, so see a doctor if it's unmanageable."
        ],
        "keywords": ["period cramps", "menstrual pain", "cramps", "period hurts", "dysmenorrhea"]
    },
    {
        "base_problem": "medication side effects",
        "answers": [
            "If you suspect you are experiencing side effects from a new medication, consult the leaflet that came with the drug to see if your symptoms are expected. Do not stop taking prescription medication abruptly without speaking to your prescribing doctor or pharmacist first, unless you are having a severe allergic reaction.",
            "Drug side effects can vary. Check your medication's information packet or call your pharmacist to verify if what you're feeling is normal. Unless you're experiencing a severe allergic reaction like hives or swelling, contact your doctor before stopping the medication.",
            "It is common for new medications to cause mild side effects initially. Review the patient information sheet provided by your pharmacy. If the side effects are severe or include difficulty breathing, seek emergency care immediately. Otherwise, call your doctor for advice."
        ],
        "keywords": ["side effects", "medication making me sick", "reaction to drug", "pill side effect"]
    },
    {
        "base_problem": "routine health screening",
        "answers": [
            "Routine health screenings are vital for preventive care. Adults should have an annual physical including blood pressure, cholesterol, and blood glucose checks. Depending on your age and gender, you may also need colonoscopies, mammograms, or prostate exams. Ask your primary care physician for a personalized schedule.",
            "Staying on top of preventive care means getting annual checkups. You should regularly check your blood pressure, cholesterol, and blood sugar. Discuss age-appropriate cancer screenings like mammograms or colonoscopies with your doctor during your visit.",
            "Checkups help catch issues early. Generally, you need yearly blood work, blood pressure monitoring, and weight checks. Your doctor will tailor a screening schedule for things like bone density or cancer screenings based on your age, gender, and family history."
        ],
        "keywords": ["health screening", "checkup", "preventive care", "what tests should I get", "annual physical"]
    }
]

TEMPLATES = [
    "I am having {keyword}",
    "I have {keyword}",
    "My {keyword} is really bad",
    "What should I do for {keyword}?",
    "How to treat {keyword} at home?",
    "I'm suffering from {keyword}",
    "Can you help with {keyword}?",
    "Remedies for {keyword}",
    "I've been experiencing {keyword} since yesterday",
    "Got a bad case of {keyword}",
    "Is there a cure for {keyword}",
    "Dealing with {keyword} right now",
    "Help me with {keyword}",
    "I feel like I have {keyword}",
    "Advice for {keyword} please",
    "I am dealing with severe {keyword}",
    "Lately I have had {keyword}",
    "Tell me how to fix {keyword}",
    "What is the best medicine for {keyword}",
    "Should I go to a doctor for {keyword}",
    "I woke up with {keyword}",
    "My husband has {keyword}",
    "My child has {keyword}",
    "Experiencing {keyword} and looking for help",
    "What causes {keyword}?",
    "How do I stop {keyword}?",
    "Any tips for {keyword}?",
    "My problem is {keyword}",
    "I've got {keyword}",
    "Need advice on {keyword}",
    "{keyword} is making me uncomfortable",
    "I cannot stand this {keyword}",
    "Constant {keyword} for the past week",
    "Sudden {keyword} appeared",
    "How long does {keyword} usually last?",
    "I'm worried about {keyword}"
]

def generate_dataset():
    dataset = []
    
    PREFIXES = ["Hello, ", "Hi doc, ", "Quick question: ", "Please help, ", "URGENT: ", ""]
    SUFFIXES = [" Thanks.", " Please reply fast.", " What do you think?", ""]
    
    for _ in range(5):  # Loop multiple times picking random prefixes/suffixes to inflate the dataset to 5000+
        for qa in QA_PAIRS:
            for keyword in qa["keywords"]:
                for template in TEMPLATES:
                    q = template.format(keyword=keyword)
                    prefix = random.choice(PREFIXES)
                    suffix = random.choice(SUFFIXES)
                    full_q = f"{prefix}{q}{suffix}".strip()
                    
                    dataset.append({
                        "question": full_q,
                        "answers": qa["answers"],
                        "base_problem": qa["base_problem"]
                    })
    
    # Deduplicate
    unique_dataset = []
    seen = set()
    for item in dataset:
        if item["question"] not in seen:
            seen.add(item["question"])
            unique_dataset.append(item)
            
    print(f"Generated {len(unique_dataset)} unique Q&A pairs.")
    
    with open(r"c:\xampp\htdocs\Healthcare Chatbot\backend\data\qa_dataset.json", "w", encoding="utf-8") as f:
        json.dump(unique_dataset, f, indent=4)
        
if __name__ == "__main__":
    generate_dataset()
