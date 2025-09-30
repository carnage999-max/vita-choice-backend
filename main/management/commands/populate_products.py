from django.core.management.base import BaseCommand
from main.models import Product
from decimal import Decimal


class Command(BaseCommand):
    help = "Populate products from predefined data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force creation even if products exist with the same name",
        )

    def handle(self, *args, **options):
        # Helper function to convert newline-separated strings to lists
        def process_field(value):
            if isinstance(value, str) and "\n" in value:
                return [item.strip() for item in value.split("\n") if item.strip()]
            return value if value is not None else []

        products_data = [
            # Stax products
            {
                "name": "Brain Stax",
                "subtitle": "Focus and clarity for busy minds",
                "price": "72.00",
                "original_price": None,
                "category": "stax",
                "rating": "4.3",
                "review_count": 89,
                "description": "Brain Stax combines nootropics and herbal extracts to improve focus, memory, and mental clarity for peak cognitive performance.",
                "short_description": "Enhances memory, focus, and mental clarity.",
                "key_actives": "Ginkgo Biloba\nL-Theanine\nBacopa Monnieri\nOmega-3 DHA",
                "free_from": "Artificial colors\nSugar\nSoy",
                "benefits": "Improves concentration\nSupports long-term brain health\nReduces mental fatigue",
                "serving_size": "1 capsule",
                "servings_per_bottle": 60,
                "usage": "Take one capsule twice daily with meals.",
                "faqs": [
                    {
                        "question": "Will Brain Stax make me jittery?",
                        "answer": "No, Brain Stax contains calming nootropics that enhance focus without overstimulation.",
                    },
                    {
                        "question": "How soon will I notice results?",
                        "answer": "Most people experience improved focus within 2-3 weeks of consistent use.",
                    },
                ],
            },
            {
                "name": "Energy Stax",
                "subtitle": "Clean, lasting energy without the crash",
                "price": "45.00",
                "original_price": None,
                "category": "stax",
                "rating": "4.1",
                "review_count": 72,
                "description": "Energy Stax provides clean, sustained energy without crashes using adaptogens and natural caffeine sources.",
                "short_description": "Boosts stamina and fights fatigue naturally.",
                "key_actives": "Green Tea Extract\nAshwagandha\nVitamin B12\nRhodiola",
                "free_from": "Gluten\nArtificial sweeteners",
                "benefits": "Increases endurance\nReduces stress-related fatigue\nSupports metabolism",
                "serving_size": "1 capsule",
                "servings_per_bottle": 60,
                "usage": "Take one capsule in the morning or before workouts.",
                "faqs": [
                    {
                        "question": "Can I take it before workouts?",
                        "answer": "Yes, Energy Stax is designed to boost stamina and focus during exercise.",
                    },
                    {
                        "question": "Does it replace coffee?",
                        "answer": "It provides natural energy and focus, so you may find you need less coffee.",
                    },
                ],
            },
            {
                "name": "Heart Stax",
                "subtitle": "Nutritional care for a stronger heart",
                "price": "66.00",
                "original_price": None,
                "category": "stax",
                "rating": "4.4",
                "review_count": 102,
                "description": "Heart Stax supports cardiovascular wellness with a blend of heart-healthy nutrients and antioxidants.",
                "short_description": "Promotes healthy heart and circulation.",
                "key_actives": "CoQ10\nHawthorn Berry\nOmega-3\nMagnesium",
                "free_from": "Dairy\nArtificial flavors",
                "benefits": "Supports healthy blood pressure\nImproves circulation\nEnhances heart function",
                "serving_size": "2 softgels",
                "servings_per_bottle": 30,
                "usage": "Take two softgels daily with food.",
                "faqs": [
                    {
                        "question": "Is Heart Stax safe with blood pressure medication?",
                        "answer": "Consult your healthcare provider before combining with prescription medications.",
                    },
                ],
            },
            {
                "name": "Cholesterol Stax",
                "subtitle": "Balance your cholesterol naturally",
                "price": "53.00",
                "original_price": None,
                "category": "stax",
                "rating": "4.0",
                "review_count": 77,
                "description": "Cholesterol Stax combines natural plant sterols and fibers to maintain healthy cholesterol levels.",
                "short_description": "Supports balanced cholesterol and heart health.",
                "key_actives": "Plant Sterols\nNiacin\nSoluble Fiber\nGarlic Extract",
                "free_from": "Soy\nGMOs",
                "benefits": "Helps lower LDL cholesterol\nPromotes healthy lipid profile\nSupports cardiovascular function",
                "serving_size": "2 tablets",
                "servings_per_bottle": 60,
                "usage": "Take two tablets daily with meals.",
                "faqs": [
                    {
                        "question": "How long does it take to see results?",
                        "answer": "It may take 8-12 weeks of consistent use to see improvements in cholesterol levels.",
                    },
                ],
            },
            {
                "name": "Diabetes Stax",
                "subtitle": "Support for balanced blood sugar",
                "price": "69.00",
                "original_price": None,
                "category": "stax",
                "rating": "4.5",
                "review_count": 141,
                "description": "Diabetes Stax is designed to support balanced blood sugar levels and metabolic function.",
                "short_description": "Helps regulate blood sugar naturally.",
                "key_actives": "Cinnamon Bark\nChromium\nAlpha Lipoic Acid\nBitter Melon",
                "free_from": "Gluten\nArtificial fillers",
                "benefits": "Supports glucose metabolism\nImproves insulin sensitivity\nPromotes energy balance",
                "serving_size": "1 capsule",
                "servings_per_bottle": 90,
                "usage": "Take one capsule before meals.",
                "faqs": [
                    {
                        "question": "Can I take it with insulin?",
                        "answer": "Check with your doctor before combining with insulin or diabetes medications.",
                    },
                ],
            },
            {
                "name": "Sleep Stax",
                "subtitle": "Relax deeper, sleep better",
                "price": "39.00",
                "original_price": None,
                "category": "stax",
                "rating": "4.7",
                "review_count": 198,
                "description": "Sleep Stax combines natural herbs and melatonin to promote restful sleep and relaxation.",
                "short_description": "Supports deeper, more restorative sleep.",
                "key_actives": "Melatonin\nValerian Root\nChamomile\nMagnesium",
                "free_from": "Dairy\nArtificial colors",
                "benefits": "Helps fall asleep faster\nImproves sleep quality\nSupports relaxation",
                "serving_size": "1 capsule",
                "servings_per_bottle": 60,
                "usage": "Take one capsule 30 minutes before bedtime.",
                "faqs": [
                    {
                        "question": "Will I feel groggy in the morning?",
                        "answer": "No, Sleep Stax is designed to promote restful sleep without morning drowsiness.",
                    },
                ],
            },
            {
                "name": "Anti-Aging Stax",
                "subtitle": "Stay youthful inside and out",
                "price": "84.00",
                "original_price": None,
                "category": "stax",
                "rating": "4.2",
                "review_count": 65,
                "description": "Anti-Aging Stax is packed with antioxidants and collagen boosters to support youthful skin, energy, and vitality.",
                "short_description": "Fights signs of aging and promotes youthful energy.",
                "key_actives": "Collagen Peptides\nResveratrol\nVitamin E\nGreen Tea Extract",
                "free_from": "Gluten\nSugar",
                "benefits": "Supports skin elasticity\nProtects against oxidative stress\nBoosts energy and vitality",
                "serving_size": "2 capsules",
                "servings_per_bottle": 60,
                "usage": "Take two capsules daily with water.",
                "faqs": [
                    {
                        "question": "Does this replace skincare products?",
                        "answer": "No, it complements a skincare routine by supporting skin health from within.",
                    },
                ],
            },
            {
                "name": "Longevity Stax",
                "subtitle": "Vitality for a long and healthy life",
                "price": "92.00",
                "original_price": None,
                "category": "stax",
                "rating": "4.8",
                "review_count": 212,
                "description": "Longevity Stax combines adaptogens and essential nutrients to support long-term vitality and healthy aging.",
                "short_description": "Promotes long life and sustained health.",
                "key_actives": "Astragalus\nCurcumin\nVitamin D3\nOmega-3",
                "free_from": "Soy\nArtificial preservatives",
                "benefits": "Supports healthy aging\nBoosts immune resilience\nMaintains vitality",
                "serving_size": "2 capsules",
                "servings_per_bottle": 60,
                "usage": "Take two capsules daily after breakfast.",
                "faqs": [
                    {
                        "question": "Is Longevity Stax suitable for seniors?",
                        "answer": "Yes, it's designed to support adults of all ages, especially those over 40.",
                    },
                ],
            },
            {
                "name": "Gut Health Stax",
                "subtitle": "Balance your digestion naturally",
                "price": "55.00",
                "original_price": None,
                "category": "stax",
                "rating": "4.5",
                "review_count": 157,
                "description": "Gut Health Stax contains probiotics and prebiotics that promote digestive balance and nutrient absorption.",
                "short_description": "Supports healthy digestion and gut flora.",
                "key_actives": "Probiotics\nPrebiotic Fiber\nDigestive Enzymes\nGinger Root",
                "free_from": "Lactose\nArtificial fillers",
                "benefits": "Restores healthy gut flora\nReduces bloating\nImproves nutrient absorption",
                "serving_size": "1 capsule",
                "servings_per_bottle": 60,
                "usage": "Take one capsule before meals.",
                "faqs": [
                    {
                        "question": "Can I take Gut Health Stax daily?",
                        "answer": "Yes, daily use is recommended for best results.",
                    },
                ],
            },
            {
                "name": "Joint & Bone Stax",
                "subtitle": "Strength and flexibility every day",
                "price": "61.00",
                "original_price": None,
                "category": "stax",
                "rating": "4.6",
                "review_count": 131,
                "description": "Joint & Bone Stax supports mobility, flexibility, and long-term joint health with minerals and collagen support.",
                "short_description": "Strengthens joints and bones for daily movement.",
                "key_actives": "Calcium\nVitamin D3\nGlucosamine\nCollagen",
                "free_from": "Dairy\nArtificial colors",
                "benefits": "Supports bone density\nPromotes joint comfort\nImproves flexibility",
                "serving_size": "2 tablets",
                "servings_per_bottle": 60,
                "usage": "Take two tablets daily with meals.",
                "faqs": [
                    {
                        "question": "Is this good for arthritis?",
                        "answer": "Yes, it helps support joint comfort and flexibility, but it's not a cure.",
                    },
                ],
            },
            {
                "name": "Men's & Women's Health Stax",
                "subtitle": "Complete daily multivitamin for both",
                "price": "74.00",
                "original_price": None,
                "category": "stax",
                "rating": "4.4",
                "review_count": 95,
                "description": "Men's & Women's Health Stax is a complete multivitamin designed to fill daily nutritional gaps for both men and women.",
                "short_description": "Daily essential multivitamin for men and women.",
                "key_actives": "Vitamin A\nB-Complex\nMagnesium\nIron",
                "free_from": "Gluten\nGMOs",
                "benefits": "Supports energy and immunity\nPromotes hormonal balance\nFills daily nutrient needs",
                "serving_size": "2 tablets",
                "servings_per_bottle": 60,
                "usage": "Take two tablets daily with meals.",
                "faqs": [
                    {
                        "question": "Can couples take this together?",
                        "answer": "Yes, it's formulated to suit both men and women equally.",
                    },
                ],
            },
            {
                "name": "Vision/Eye Health Stax",
                "subtitle": "Protect your vision daily",
                "price": "47.00",
                "original_price": None,
                "category": "stax",
                "rating": "4.3",
                "review_count": 83,
                "description": "Vision/Eye Health Stax is formulated with antioxidants and carotenoids to protect eye health and reduce eye strain.",
                "short_description": "Supports eye health and reduces strain.",
                "key_actives": "Lutein\nZeaxanthin\nVitamin A\nBilberry Extract",
                "free_from": "Dairy\nGluten",
                "benefits": "Protects retinal health\nReduces digital eye strain\nSupports long-term vision",
                "serving_size": "1 capsule",
                "servings_per_bottle": 60,
                "usage": "Take one capsule daily with water.",
                "faqs": [
                    {
                        "question": "Is it safe for screen users?",
                        "answer": "Yes, it's especially beneficial for those exposed to long hours of screen time.",
                    },
                ],
            },
            # Premium products
            {
                "name": "Vita-Choice™ Core Liquid Multivitamin",
                "subtitle": "Fully Methylated",
                "price": "149.00",
                "original_price": "179.00",
                "category": "Daily Essentials",
                "rating": "4.9",
                "review_count": 2847,
                "description": "A premium, fully methylated, gluten-free, vegan liquid multivitamin base with synergistic cofactors and superfoods (spirulina, seaweed). Designed for high bioavailability and gentle daily use.",
                "short_description": "One premium liquid base. Fully methylated B-complex, bioavailable minerals, and synergistic co-factors for whole-body support. Clean, efficient, daily.",
                "key_actives": [
                    "Methylfolate (5-MTHF) - 400mcg",
                    "Methylcobalamin (B12) - 500mcg",
                    "P5P (Active B6) - 25mg",
                    "Chelated Magnesium - 200mg",
                    "Zinc (Bisglycinate) - 15mg",
                    "Selenium (Methionine) - 200mcg",
                    "Iodine (Kelp) - 150mcg",
                    "Vitamin D3 - 2000 IU (adjustable)",
                    "Spirulina Complex - 500mg",
                    "Seaweed Blend - 300mg",
                ],
                "free_from": [
                    "Gluten",
                    "Artificial colors",
                    "Artificial sweeteners",
                    "GMOs",
                    "Dairy",
                    "Soy",
                ],
                "benefits": [
                    "Energy metabolism support",
                    "Cognitive clarity enhancement",
                    "Stress resilience building",
                    "Immune system support",
                ],
                "serving_size": "1 tablespoon (15ml)",
                "servings_per_bottle": 30,
                "usage": "Take 1 tablespoon daily with food, preferably in the morning. Can be taken directly or mixed with water or juice.",
                "faqs": [
                    {
                        "question": "How is this different from regular multivitamins?",
                        "answer": "Our liquid formula uses fully methylated forms of vitamins that bypass genetic variations (like MTHFR) that prevent proper absorption of synthetic vitamins. Plus, liquid absorption is 95%+ vs 10-20% for pills.",
                    },
                    {
                        "question": "Is this safe to take with medications?",
                        "answer": "While generally safe, we recommend consulting your healthcare provider before starting any new supplement, especially if you take medications or have health conditions.",
                    },
                    {
                        "question": "Can I customize the dosage?",
                        "answer": "Yes! Based on your health assessment and lab work, our medical team can adjust concentrations of key nutrients like Vitamin D, B12, and minerals to meet your specific needs.",
                    },
                ],
            },
            {
                "name": "Diabetes Support Stack",
                "subtitle": "Targeted Nutritional Formula",
                "price": "179.00",
                "original_price": "199.00",
                "category": "Condition Support",
                "rating": "4.7",
                "review_count": 1132,
                "description": "Targeted nutrients supporting insulin sensitivity, glucose metabolism, mitochondrial function, and gut balance. Includes specific pre-/probiotics, cinnamon extract, chromium, and other evidence-aligned actives.",
                "short_description": "A complete, evidence-based support system for healthy glucose metabolism and energy balance.",
                "key_actives": [
                    "Cinnamon Extract - 500mg",
                    "Chromium Picolinate - 200mcg",
                    "Berberine - 300mg",
                    "Probiotic Blend - 10B CFU",
                    "Alpha Lipoic Acid - 200mg",
                ],
                "free_from": ["Gluten", "Dairy", "Soy", "Artificial additives"],
                "benefits": [
                    "Improves insulin sensitivity",
                    "Supports glucose metabolism",
                    "Enhances mitochondrial efficiency",
                    "Promotes gut microbiome balance",
                ],
                "serving_size": "2 capsules daily",
                "servings_per_bottle": 60,
                "usage": "Take 2 capsules daily with meals, or as directed by your healthcare provider.",
                "faqs": [
                    {
                        "question": "Can this replace my diabetes medication?",
                        "answer": "No. This stack is intended as a nutritional support supplement. Always continue prescribed medication unless your doctor advises otherwise.",
                    },
                    {
                        "question": "How soon can I expect results?",
                        "answer": "Many users report improved energy and glucose stability within 4–6 weeks, though individual results vary.",
                    },
                ],
            },
            {
                "name": "Microplastics Cleanse Stack",
                "subtitle": "Environmental Detox Formula",
                "price": "189.00",
                "original_price": "209.00",
                "category": "Detox & Cleanse",
                "rating": "4.8",
                "review_count": 894,
                "description": "Supports binding, mobilization, and elimination pathways; promotes gut barrier integrity and antioxidant defense for modern environmental exposures.",
                "short_description": "Science-based detox formulation targeting microplastic and toxin exposure.",
                "key_actives": [
                    "Chlorella - 1000mg",
                    "Activated Charcoal - 500mg",
                    "Glutathione - 250mg",
                    "Quercetin - 150mg",
                    "L-Glutamine - 1g",
                ],
                "free_from": ["GMOs", "Artificial additives", "Soy", "Dairy"],
                "benefits": [
                    "Binds and removes microplastics",
                    "Strengthens gut barrier integrity",
                    "Boosts antioxidant defenses",
                    "Supports liver detox pathways",
                ],
                "serving_size": "3 capsules daily",
                "servings_per_bottle": 90,
                "usage": "Take 3 capsules daily with water. For intensive detox protocols, consult a healthcare provider.",
                "faqs": [
                    {
                        "question": "Is this safe for daily use?",
                        "answer": "Yes, but we recommend periodic use (8–12 weeks) followed by breaks, depending on exposure and lifestyle factors.",
                    },
                    {
                        "question": "Can I combine this with probiotics?",
                        "answer": "Absolutely. Probiotics may further support gut barrier health alongside the cleanse.",
                    },
                ],
            },
            {
                "name": "Daily Dosing Device",
                "subtitle": "Precision Liquid Dispenser",
                "price": "89.00",
                "original_price": "109.00",
                "category": "Accessories",
                "rating": "4.6",
                "review_count": 542,
                "description": "A precision-engineered device designed for accurate daily liquid supplement dosing. Ensures consistent serving size and minimal mess, perfect for maintaining your supplement routine.",
                "short_description": "Accurate, mess-free, and convenient liquid dosing for daily supplement use.",
                "key_actives": [
                    "Engineered dispenser mechanism",
                    "Calibrated markings",
                    "BPA-free, food-safe materials",
                ],
                "free_from": ["BPA", "Phthalates", "Lead"],
                "benefits": [
                    "Precise liquid measurement",
                    "Mess-free dispensing",
                    "Durable, medical-grade materials",
                    "Easy cleaning & maintenance",
                ],
                "serving_size": "Variable per use",
                "servings_per_bottle": None,
                "usage": "Use to measure and dispense the exact serving size of liquid supplements daily.",
                "faqs": [
                    {
                        "question": "Is this dishwasher safe?",
                        "answer": "Yes, it is fully dishwasher safe for easy cleaning.",
                    },
                    {
                        "question": "Can it be used for other liquids?",
                        "answer": "Yes, it can be used for most dietary supplement liquids, oils, or tinctures.",
                    },
                ],
            },
        ]

        created_count = 0
        skipped_count = 0

        for product_data in products_data:
            # Check if product already exists (skip Immune Stax as mentioned)
            if Product.objects.filter(name=product_data["name"]).exists():
                if not options["force"]:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Product "{product_data["name"]}" already exists. Skipping...'
                        )
                    )
                    skipped_count += 1
                    continue
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Product "{product_data["name"]}" already exists. Forcing creation...'
                        )
                    )

            try:
                # Convert price fields to Decimal
                price = Decimal(str(product_data["price"]))
                original_price = None
                if product_data.get("original_price"):
                    original_price = Decimal(str(product_data["original_price"]))

                # Convert rating to Decimal
                rating = Decimal(str(product_data["rating"]))

                # Process fields that might be strings with newlines or lists
                key_actives = process_field(product_data.get("key_actives", []))
                free_from = process_field(product_data.get("free_from", []))
                benefits = process_field(product_data.get("benefits", []))

                # Create product
                product = Product.objects.create(
                    name=product_data["name"],
                    subtitle=product_data.get("subtitle", ""),
                    price=price,
                    original_price=original_price,
                    category=product_data["category"],
                    rating=rating,
                    review_count=product_data.get("review_count", 0),
                    description=product_data.get("description", ""),
                    short_description=product_data.get("short_description", ""),
                    key_actives=key_actives,
                    free_from=free_from,
                    benefits=benefits,
                    serving_size=product_data.get("serving_size", ""),
                    servings_per_bottle=product_data.get("servings_per_bottle"),
                    faqs=product_data.get("faqs", []),
                    usage=product_data.get("usage", ""),
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created product: "{product.name}"'
                    )
                )
                created_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error creating product "{product_data["name"]}": {str(e)}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary: {created_count} products created, {skipped_count} products skipped."
            )
        )
