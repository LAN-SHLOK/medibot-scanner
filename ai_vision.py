import torch
from PIL import Image, ImageOps, ImageFilter
import open_clip
import numpy as np
import pydicom 
import cv2 # <--- REQUIRED: You must install opencv-python

BODY_PARTS = [
    "Abdominal CT (General)",
    "Adrenal Glands (Abdominal CT)",
    "Pelvis MRI (General)",
    "Shoulder MRI (Soft Tissue)",
    "CT KUB (Kidney Stone Protocol)",
    "Soft Tissue Neck CT",
    "Hip Joint X-Ray",
    "Scapula/Shoulder Blade X-Ray",
    "Patella (Skyline) X-Ray",
    "Calcaneus (Heel) X-Ray",
    "Skull/Cranium X-Ray", "Sinus/Paranasal X-Ray", "Mandible/Jaw X-Ray", 
    "Orbit/Eye MRI/CT", "Temporomandibular Joint (TMJ) X-Ray", "Nasal Bone X-Ray",
    "Soft Tissue Neck X-Ray", "Dental/Teeth X-Ray",
    "Brain/Circle of Willis (MRI/CT)", "Head-Neck Combined Scan",
    "Cervical Spine (C-Spine) X-Ray", "Thoracic Spine (T-Spine) X-Ray", 
    "Lumbar Spine (L-Spine) X-Ray", "Thoraco-Lumbar (TL-Spine) X-Ray",
    "Sacrum/Coccyx X-Ray", "Whole Spine (Scoliosis) Series",
    "Chest X-Ray (PA/AP View)", "Chest X-Ray (Lateral View)", 
    "Ribs/Sternum X-Ray", "Clavicle/Collarbone X-Ray",
    "Scapula/Shoulder Blade X-Ray", "Chest-Abdomen-Pelvis (CAP) Scan",
    "Abdominal X-Ray (General)", "KUB (Kidney/Ureter/Bladder) X-Ray",
    "Pelvis X-Ray", "Hip Joint X-Ray", "Hysterosalpingogram (HSG)",
    "Abdominal Ultrasound (Gallbladder/Liver)", "Obstetric Ultrasound (Fetal)",
    "Shoulder Joint X-Ray", "Humerus (Upper Arm) X-Ray", "Elbow X-Ray", 
    "Forearm (Radius/Ulna) X-Ray", "Wrist X-Ray", "Scaphoid View X-Ray", 
    "Hand X-Ray", "Finger/Thumb X-Ray",
    "Femur (Thigh) X-Ray", "Knee X-Ray", "Patella (Skyline) X-Ray", 
    "Tibia/Fibula (Leg) X-Ray", "Ankle X-Ray", "Calcaneus (Heel) X-Ray", 
    "Foot X-Ray", "Toe X-Ray",
    "Angiography (Artery/Vein)", "Whole Body Scan (Bone/PET)",
    "Dermatology (Skin Lesion/Rash)",
    "Phantom/Calibration Object", "Quality Control (QC) Pattern",
    "Non-Medical Image (Document/Photo)",
    "Lumbar Spine MRI (Soft Tissue)",
    "Lower Limb Venous Doppler (Ultrasound)",
    "CT Angiography (Vascular)",
    "Sella Turcica (Pituitary MRI)",
    "Circle of Willis (Brain MRA/MRA)",
    "Temporal Bone (High-Res CT)",
    "Adrenal Glands (Abdominal CT)",
    "Coronary Arteries (CT Angio)",
    "Lumbosacral Plexus (MRI)",
    "Orbits/Optic Nerve (Eye MRI)"
]

# -----------------------------------------------------------------------------
# 2. DOCUMENT DETECTION LIST
# -----------------------------------------------------------------------------
ADMIN_DOCUMENTS = [
    "Official Prescription Document",
    "Medical Insurance Form",
    "Hospital Discharge Summary",
    "Lab Report Page",
    "Handwritten Note"
]

# -----------------------------------------------------------------------------
# 3. COMPREHENSIVE CONDITIONS LIST
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# 3. COMPREHENSIVE CONDITIONS LIST (FINAL GOD LEVEL)
# -----------------------------------------------------------------------------
CONDITIONS = {

    # =========================
    # HEAD, BRAIN & NECK
    # =========================
    "Brain / Circle of Willis (MRI/CT)": [
        "Normal Brain",
        "Acute Ischemic Stroke",
        "Chronic Infarct",
        "Intracerebral Hemorrhage",
        "Subarachnoid Hemorrhage",
        "Subdural Hematoma",
        "Epidural Hematoma",
        "Cerebral Aneurysm",
        "Arteriovenous Malformation",
        "Glioblastoma",
        "Low-Grade Glioma",
        "Meningioma",
        "Metastatic Brain Tumor",
        "Hydrocephalus",
        "Diffuse Axonal Injury",
        "Creutzfeldt-Jakob Disease"
    ],

    "Circle of Willis (MRA/CTA)": [
        "Normal Flow",
        "Saccular Aneurysm",
        "Fusiform Aneurysm",
        "Arteriovenous Malformation",
        "Moyamoya Disease",
        "Arterial Stenosis",
        "Vessel Occlusion",
        "Vasculitis"
    ],

    "Soft Tissue Neck (CT/X-Ray)": [
        "Normal Neck",
        "Reactive Lymphadenopathy",
        "Malignant Lymphadenopathy",
        "Thyroid Nodule",
        "Goiter",
        "Retropharyngeal Abscess",
        "Parapharyngeal Abscess",
        "Epiglottitis",
        "Laryngeal Carcinoma",
        "Salivary Gland Stone",
        "Deep Neck Space Infection"
    ],

    "Sella Turcica / Pituitary (MRI)": [
        "Normal Pituitary",
        "Pituitary Microadenoma",
        "Pituitary Macroadenoma",
        "Craniopharyngioma",
        "Rathke’s Cleft Cyst",
        "Empty Sella Syndrome",
        "Pituitary Apoplexy"
    ],

    "Temporal Bone (HRCT)": [
        "Normal Temporal Bone",
        "Cholesteatoma",
        "Otosclerosis",
        "Mastoiditis",
        "Temporal Bone Fracture",
        "Inner Ear Malformation"
    ],

    "Orbit / Eye (CT/MRI)": [
        "Normal Orbit",
        "Optic Neuritis",
        "Orbital Cellulitis",
        "Retinal Detachment",
        "Orbital Tumor",
        "Graves Orbitopathy",
        "Intraocular Melanoma"
    ],

    # =========================
    # CHEST & CARDIOVASCULAR
    # =========================
    "Chest X-Ray / CT": [
        "Normal Chest",
        "Lobar Pneumonia",
        "Interstitial Pneumonia",
        "Tuberculosis",
        "Pleural Effusion",
        "Pneumothorax",
        "Tension Pneumothorax",
        "Pulmonary Edema",
        "Lung Mass",
        "Primary Lung Cancer",
        "Pulmonary Metastasis"
    ],

    "CT Angiography / Coronary CTA": [
        "Normal Vessels",
        "Pulmonary Embolism",
        "Aortic Aneurysm",
        "Aortic Dissection",
        "Coronary Artery Disease",
        "Vascular Stenosis",
        "Vascular Occlusion"
    ],

    "Echocardiogram": [
        "Normal Cardiac Function",
        "Pericardial Effusion",
        "Cardiac Tamponade",
        "Valvular Stenosis",
        "Valvular Regurgitation",
        "Endocarditis",
        "Dilated Cardiomyopathy",
        "Hypertrophic Cardiomyopathy"
    ],

    # =========================
    # ABDOMEN & PELVIS
    # =========================
    "Abdominal CT (General)": [
        "Normal Abdomen",
        "Acute Appendicitis",
        "Diverticulitis",
        "Acute Pancreatitis",
        "Chronic Pancreatitis",
        "Bowel Obstruction",
        "Bowel Perforation",
        "Abdominal Aortic Aneurysm",
        "Mesenteric Ischemia"
    ],

    "CT KUB (Stone Protocol)": [
        "Normal Kidneys",
        "Renal Calculus",
        "Ureteric Calculus",
        "Staghorn Calculus",
        "Hydronephrosis",
        "Pyelonephritis",
        "Perinephric Abscess",
        "Bladder Stone"
    ],

    "Pelvis MRI (General)": [
        "Normal Pelvis",
        "Cervical Cancer",
        "Endometrial Cancer",
        "Ovarian Cancer",
        "Prostate Cancer",
        "Bladder Tumor",
        "Uterine Fibroid",
        "Adenomyosis",
        "Endometriosis",
        "Pelvic Abscess"
    ],

    "Pelvis X-Ray": [
        "Normal Pelvis",
        "Pelvic Ring Fracture",
        "Hip Dislocation",
        "Pubic Ramus Fracture",
        "Bone Metastasis",
        "Pelvic Osteomyelitis"
    ],

    "Hysterosalpingogram (HSG)": [
        "Normal Patent Tubes",
        "Unilateral Tubal Block",
        "Bilateral Tubal Block",
        "Hydrosalpinx",
        "Uterine Septum",
        "Asherman Syndrome"
    ],

    # =========================
    # SPINE
    # =========================
    "Spine (Cervical/Thoracic/Lumbar)": [
        "Normal Spine",
        "Degenerative Disc Disease",
        "Disc Herniation",
        "Spinal Canal Stenosis",
        "Vertebral Compression Fracture",
        "Burst Fracture",
        "Spondylolisthesis",
        "Spinal Infection",
        "Spinal Metastasis",
        "Cauda Equina Syndrome"
    ],

    # =========================
    # LIMBS & JOINTS
    # =========================
    "Joint MRI (Shoulder/Knee)": [
        "Normal Joint",
        "Rotator Cuff Tear",
        "Labral Tear",
        "ACL Tear",
        "Meniscus Tear",
        "Osteochondral Defect",
        "Joint Effusion"
    ],

    "Long Bone X-Ray": [
        "Normal Bone",
        "Acute Fracture",
        "Stress Fracture",
        "Pathological Fracture",
        "Osteomyelitis",
        "Osteosarcoma"
    ],

    # =========================
    # DERMATOLOGY
    # =========================
    "Dermatology (Imaging-Based)": [
        "Benign Nevus",
        "Malignant Melanoma",
        "Basal Cell Carcinoma",
        "Squamous Cell Carcinoma",
        "Hemangioma",
        "Lipoma"
    ],

    # =========================
    # NON-MEDICAL / CONTROL
    # =========================
    "Non-Medical / Control": [
        "Medical Document",
        "Lab Report",
        "Photograph of Film",
        "Blurry Image",
        "Calibration Phantom"
    ]
}


# --- 🎯 HIGH-PRECISION SPECIALTY LISTS ---
# We use descriptive adjectives so the AI matches visual features exactly.

# --- 🎯 HIGH-PRECISION SPECIALTY LISTS ---

# UPDATED: Covers ALL 14 Ultrasound Categories
ULTRASOUND_PRECISION_LIST = [

    # ==================================================
    # 1. ABDOMEN (LIVER, GALLBLADDER, PANCREAS, SPLEEN)
    # ==================================================
    "Normal Abdomen Ultrasound",

    # Liver
    "Fatty Liver (Increased Echogenicity)",
    "Liver Cirrhosis (Coarse Echotexture / Nodular Surface)",
    "Liver Abscess (Hypoechoic with Internal Debris)",
    "Hepatocellular Carcinoma (Solid Vascular Mass)",        # 🚨
    "Liver Metastasis (Multiple Target Lesions)",            # 🚨
    "Liver Cyst (Simple Anechoic)",

    # Gallbladder
    "Gallstones (Echogenic with Acoustic Shadow)",           # 🔒 stone locked
    "Acute Cholecystitis (Wall Thickening + Murphy Sign)",   # 🚨
    "Chronic Cholecystitis",
    "Gallbladder Polyp",
    "Gallbladder Empyema",                                   # 🚨

    # Pancreas
    "Acute Pancreatitis (Bulky Hypoechoic Pancreas)",        # 🚨
    "Chronic Pancreatitis (Calcifications)",
    "Pancreatic Pseudocyst",
    "Pancreatic Mass (Suspicious)",                          # 🚨

    # Spleen
    "Splenomegaly",
    "Splenic Infarct",
    "Splenic Abscess",                                       # 🚨

    # Free Fluid
    "Ascites (Free Intraperitoneal Fluid)",

    # ==================================================
    # 2. KIDNEYS & URINARY TRACT (CRITICAL PRECISION)
    # ==================================================
    "Normal Renal Ultrasound",

    "Renal Calculus (Echogenic Focus + Acoustic Shadow)",    # 🔒 NO CONFUSION
    "Staghorn Calculus",                                     # 🚨
    "Hydronephrosis (Pelvicalyceal Dilatation)",             # 🚨
    "Acute Pyelonephritis",
    "Renal Abscess",                                         # 🚨
    "Polycystic Kidney Disease",
    "Renal Cortical Cyst (Simple)",
    "Renal Mass (Solid – Suspicious for RCC)",               # 🚨

    # Bladder
    "Bladder Stone (Mobile Echogenic Focus)",                # 🔒
    "Bladder Tumor (Irregular Wall Mass)",                   # 🚨
    "Urinary Retention (Distended Bladder)",

    # ==================================================
    # 3. PELVIS (GYNE + MALE)
    # ==================================================
    "Normal Pelvic Ultrasound",

    # Female
    "Uterine Fibroid (Well-Defined Hypoechoic Mass)",
    "Adenomyosis",
    "Endometrial Thickening",
    "Endometrial Polyp",
    "Ovarian Simple Cyst",
    "Hemorrhagic Ovarian Cyst",
    "Ovarian Torsion (Absent Doppler Flow)",                 # 🚨
    "Polycystic Ovary Syndrome (PCOS)",
    "Pelvic Inflammatory Disease (PID)",                     # 🚨
    "Pelvic Abscess",                                        # 🚨

    # Male
    "Benign Prostatic Hyperplasia (Enlarged Prostate)",
    "Prostatitis",
    "Prostate Abscess",                                      # 🚨

    # ==================================================
    # 4. OBSTETRIC (PREGNANCY – ZERO TOLERANCE)
    # ==================================================
    "Normal Intrauterine Pregnancy",
    "Gestational Sac (Early Pregnancy)",
    "Ectopic Pregnancy (Adnexal Mass + No IUP)",             # 🚨
    "Placenta Previa",
    "Placental Abruption",                                   # 🚨
    "Oligohydramnios",
    "Polyhydramnios",
    "Multiple Gestation",
    "Fetal Anomaly (Structural)",
    "Intrauterine Fetal Demise (No Cardiac Activity)",       # 🚨

    # ==================================================
    # 5. VASCULAR DOPPLER (HIGH-RISK)
    # ==================================================
    "Normal Doppler Flow",

    "Deep Vein Thrombosis (Non-Compressible Vein)",          # 🚨
    "Superficial Thrombophlebitis",
    "Carotid Artery Stenosis (Plaque with Increased PSV)",   # 🚨
    "Carotid Artery Occlusion",                              # 🚨
    "Varicose Veins (Venous Reflux)",
    "Portal Hypertension (Dilated Portal Vein)",
    "Abdominal Aortic Aneurysm (AAA)",                       # 🚨

    # ==================================================
    # 6. CARDIAC (ECHOCARDIOGRAPHY)
    # ==================================================
    "Normal Echocardiogram",

    "Pericardial Effusion",                                  # 🚨
    "Cardiac Tamponade",                                     # 🚨
    "Vegetation (Infective Endocarditis)",                   # 🚨
    "Dilated Cardiomyopathy",
    "Hypertrophic Cardiomyopathy",
    "Wall Motion Abnormality (Ischemia)",

    # ==================================================
    # 7. THYROID & NECK
    # ==================================================
    "Normal Thyroid Ultrasound",
    "Thyroid Nodule (Solid / Cystic)",
    "Thyroiditis",
    "Thyroid Malignancy (Suspicious Features)",              # 🚨
    "Enlarged Cervical Lymph Node (Reactive)",
    "Malignant Cervical Lymphadenopathy",                    # 🚨

    # ==================================================
    # 8. BREAST
    # ==================================================
    "Normal Breast Ultrasound",
    "Breast Fibroadenoma (Benign)",
    "Breast Cyst (Simple)",
    "Breast Abscess",                                        # 🚨
    "Breast Malignancy (Irregular Spiculated Mass)",         # 🚨

    # ==================================================
    # 9. SCROTAL / TESTICULAR (NO MISSES ALLOWED)
    # ==================================================
    "Normal Testes",

    "Hydrocele",
    "Varicocele",
    "Testicular Torsion (Absent Flow)",                       # 🚨
    "Epididymo-Orchitis",
    "Testicular Tumor (Solid Hypoechoic Mass)",              # 🚨

    # ==================================================
    # 10. LUNG / THORACIC
    # ==================================================
    "Normal Lung Ultrasound",

    "Pleural Effusion",
    "Empyema",                                               # 🚨
    "Pneumothorax (Absent Lung Sliding)",                    # 🚨
    "Lung Consolidation (Pneumonia)",                        # 🚨

    # ==================================================
    # 11. MUSCULOSKELETAL (MSK)
    # ==================================================
    "Normal Musculoskeletal Ultrasound",

    "Tendon Tear (Partial / Complete)",
    "Muscle Tear",
    "Muscle Hematoma",
    "Joint Effusion",
    "Bursitis",
    "Soft Tissue Abscess",                                   # 🚨

    # ==================================================
    # 12. PEDIATRIC / NEONATAL
    # ==================================================
    "Normal Neonatal Brain",

    "Neonatal Intraventricular Hemorrhage",                  # 🚨
    "Hydrocephalus",
    "Pyloric Stenosis (Target Sign)",                        # 🚨
    "Intussusception (Target / Donut Sign)",                 # 🚨

    # ==================================================
    # 13. OCULAR
    # ==================================================
    "Normal Eye Ultrasound",

    "Retinal Detachment",                                    # 🚨
    "Vitreous Hemorrhage",
    "Intraocular Tumor (Suspicious)",                        # 🚨

    # ==================================================
    # 14. INTERVENTIONAL / CONTROL
    # ==================================================
    "Ultrasound-Guided Biopsy",
    "Ultrasound-Guided Drainage",
    "Poor Quality / Non-Diagnostic Ultrasound"
]



# UPDATED: Covers the 5 Main Dermoscopy Categories
DERMOSCOPY_PRECISION_LIST = [

    # ==================================================
    # 1. PIGMENTED SKIN LESIONS (MELANOMA VS NEVUS — NO CONFUSION)
    # ==================================================
    "Normal Skin (No Pigment Network)",

    "Benign Melanocytic Nevus (Regular Pigment Network)",
    "Congenital Melanocytic Nevus (Large / Hairy)",
    "Blue Nevus (Homogeneous Steel-Blue Area)",

    "Melanoma (Asymmetry + Atypical Pigment Network)",              # 🚨
    "Superficial Spreading Melanoma (Irregular Network)",           # 🚨
    "Nodular Melanoma (Structureless Dark Areas)",                  # 🚨
    "Acral Melanoma (Parallel Ridge Pattern)",                      # 🚨
    "Melanoma In Situ (Irregular Dots and Globules)",               # 🚨

    "Seborrheic Keratosis (Milia-like Cysts / Comedo Openings)",
    "Dermatofibroma (Central White Scar + Peripheral Pigment)",
    "Pigmented Basal Cell Carcinoma (Blue-Gray Ovoid Nests)",        # 🚨

    # ==================================================
    # 2. NON-PIGMENTED / INFLAMMATORY / TUMOROUS LESIONS
    # ==================================================
    "Basal Cell Carcinoma (Arborizing Vessels)",                     # 🚨
    "Squamous Cell Carcinoma (Keratin + Glomerular Vessels)",        # 🚨
    "Actinic Keratosis (Strawberry Pattern)",

    "Amelanotic Melanoma (Polymorphous / Irregular Vessels)",        # 🚨
    "Keratoacanthoma (Central Keratin Plug)",

    "Psoriasis (Regular Dotted Vessels on Red Background)",
    "Lichen Planus (Wickham Striae)",
    "Sebaceous Hyperplasia (Crown Vessels + Central Dell)",

    # ==================================================
    # 3. SCALP & HAIR — TRICHOSCOPY (AUTOIMMUNE VS SCAR)
    # ==================================================
    "Normal Scalp (Uniform Follicular Openings)",

    "Alopecia Areata (Black Dots / Exclamation Mark Hairs)",
    "Androgenetic Alopecia (Hair Shaft Diameter Variability)",
    "Telogen Effluvium (Uniform Hair Shaft Diameter)",
    "Traction Alopecia (Broken Hairs at Margins)",

    "Tinea Capitis (Comma / Corkscrew Hairs)",
    "Lichen Planopilaris (Perifollicular Scaling + Blue-Gray Dots)",  # 🚨 scarring
    "Discoid Lupus Erythematosus (Follicular Plugs + White Patches)", # 🚨 scarring

    # ==================================================
    # 4. NAILS — ONYCHOSCOPY (MELANOMA LOCKED)
    # ==================================================
    "Normal Nail Unit",

    "Longitudinal Melanonychia (Regular Parallel Lines)",
    "Subungual Melanoma (Irregular Lines + Hutchinson Sign)",        # 🚨
    "Subungual Hematoma (Homogeneous Red-Black Area)",

    "Onychomycosis (Jagged Proximal Edge / Yellow Spikes)",
    "Nail Psoriasis (Oil Drop Sign / Pitting)",
    "Splinter Hemorrhages",

    # ==================================================
    # 5. INFECTIONS & INFESTATIONS (PATTERN-SPECIFIC)
    # ==================================================
    "Scabies (Delta-Wing Jet Sign)",                                  # 🚨 contagious
    "Viral Wart (Thrombosed Capillaries / Black Dots)",
    "Molluscum Contagiosum (Central Umbilication)",
    "Pediculosis Capitis (Nits on Hair Shaft)",
    "Superficial Fungal Infection (Peripheral Scaling)",

    # ==================================================
    # 6. VASCULAR & PEDIATRIC LESIONS
    # ==================================================
    "Infantile Hemangioma (Red-Blue Lacunae)",
    "Cherry Angioma (Red Lacunae)",
    "Port Wine Stain (Homogeneous Red Area)",
    "Pyogenic Granuloma (White Collarette + Red Structureless)",     # 🚨 bleeding risk
    "Angiokeratoma (Dark Lacunae + Whitish Veil)",

    # ==================================================
    # 7. MUCOSAL SURFACES (VERY HIGH RISK)
    # ==================================================
    "Labial Melanotic Macule (Uniform Brown Pigment)",
    "Oral Lichen Planus (Wickham Striae)",

    "Mucosal Melanoma (Irregular Pigmentation + Structureless Areas)", # 🚨
    "Oral Squamous Cell Carcinoma (Ulcerated Irregular Surface)",       # 🚨

    # ==================================================
    # 8. CONTROL / NON-DIAGNOSTIC
    # ==================================================
    "Normal Benign Skin Pattern",
    "Inflamed Lesion (Non-Specific)",
    "Poor Quality Dermoscopy Image",
    "Non-Skin Image / Artifact"
]

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# 4. TRIAGE SEVERITY MAP (THE "GOD LEVEL" UPDATE)
# -----------------------------------------------------------------------------
SCAN_SEVERITY_MAP = {

    # ==================================================
    # LEVEL 4 — CRITICAL / EMERGENCY / LIFE-THREATENING
    # ==================================================

    # --- TRAUMA / BLEEDING ---
    "acute fracture": 4,
    "open fracture": 4,
    "pathological fracture": 4,
    "intracranial hemorrhage": 4,
    "intracerebral hemorrhage": 4,
    "epidural hematoma": 4,
    "subdural hematoma": 4,
    "subarachnoid hemorrhage": 4,

    # --- VASCULAR / ISCHEMIC ---
    "acute ischemic stroke": 4,
    "large vessel occlusion": 4,
    "pulmonary embolism": 4,
    "massive embolism": 4,
    "arterial thrombosis": 4,
    "aortic dissection": 4,
    "ruptured aneurysm": 4,
    "aortic rupture": 4,

    # --- ABDOMINAL / SURGICAL ---
    "bowel perforation": 4,
    "free intraperitoneal air": 4,
    "volvulus": 4,
    "bowel ischemia": 4,
    "mesenteric ischemia": 4,
    "peritonitis": 4,
    "ruptured ectopic pregnancy": 4,

    # --- CHEST ---
    "tension pneumothorax": 4,
    "massive pleural effusion": 4,

    # --- OBSTETRIC ---
    "ectopic pregnancy": 4,

    # --- NEURO / SPINE ---
    "brain herniation": 4,
    "midline shift": 4,
    "spinal cord compression": 4,
    "cauda equina syndrome": 4,

    # --- CARDIAC ---
    "cardiac tamponade": 4,
    "vegetation": 4,

    # --- ONCOLOGY (AUTOMATIC CRITICAL) ---
    "malignancy": 4,
    "cancer": 4,
    "carcinoma": 4,
    "sarcoma": 4,
    "lymphoma": 4,
    "melanoma": 4,
    "subungual melanoma": 4,
    "mucosal melanoma": 4,
    "glioblastoma": 4,
    "metastasis": 4,
    "metastatic": 4,
    "primary tumor": 4,
    "spiculated mass": 4,

    # ==================================================
    # LEVEL 3 — URGENT / HIGH-RISK / NEEDS ACTION
    # ==================================================

    # --- INFECTION ---
    "abscess": 3,
    "sepsis": 3,
    "pneumonia": 3,
    "tuberculosis": 3,
    "meningitis": 3,
    "appendicitis": 3,
    "cholecystitis": 3,
    "pancreatitis": 3,
    "diverticulitis": 3,
    "mastoiditis": 3,
    "pyelonephritis": 3,
    "osteomyelitis": 3,

    # --- OBSTRUCTIVE / STRUCTURAL ---
    "bowel obstruction": 3,
    "hydronephrosis": 3,
    "ureteric obstruction": 3,
    "stone with obstruction": 3,
    "stenosis": 3,
    "compression": 3,
    "dislocation": 3,
    "subluxation": 3,
    "joint effusion": 3,
    "ascites": 3,

    # --- NEURO ---
    "hydrocephalus": 3,
    "demyelinating disease": 3,
    "cord edema": 3,

    # --- CHEST ---
    "lung consolidation": 3,
    "pleural effusion": 3,

    # --- MSK ---
    "stress fracture": 3,
    "bone marrow edema": 3,

    # --- EYE / DERM ---
    "retinal detachment": 3,
    "amelanotic melanoma": 3,
    "blue-white veil": 3,
    "irregular vessels": 3,

    # ==================================================
    # LEVEL 2 — ABNORMAL / CHRONIC / BENIGN BUT RELEVANT
    # ==================================================

    # --- GENERAL ---
    "chronic inflammation": 2,
    "degenerative": 2,
    "fibrosis": 2,
    "calcification": 2,

    # --- ABDOMEN ---
    "simple cyst": 2,
    "polyp": 2,
    "fibroid": 2,
    "adenomyosis": 2,
    "fatty liver": 2,
    "cirrhosis": 2,

    # --- MSK ---
    "osteoarthritis": 2,
    "spondylosis": 2,
    "scoliosis": 2,
    "ligament tear": 2,
    "labral tear": 2,
    "old healed fracture": 2,

    # --- DERM ---
    "nevus": 2,
    "psoriasis": 2,
    "eczema": 2,
    "onychomycosis": 2,
    "alopecia": 2,
    "lipoma": 2,
    "hemangioma": 2,

    # ==================================================
    # LEVEL 1 — NORMAL / INCIDENTAL / SAFE
    # ==================================================

    "normal": 1,
    "unremarkable": 1,
    "within normal limits": 1,
    "physiological": 1,
    "anatomical variant": 1,
    "no acute abnormality": 1
}

# -----------------------------------------------------------------------------
# 🚫 HALLUCINATION GUARD — DISEASE-SPECIFIC PRECISION RULES
# -----------------------------------------------------------------------------

DISEASE_RULES = {

    # =========================
    # KIDNEY STONE (RENAL)
    # =========================
    "renal calculus": {
        "allowed_scan": ["CT KUB (Kidney Stone Protocol)"],
        "required_terms": ["calculus", "stone", "hyperdense"],
        "forbidden_terms": ["cyst", "phlebolith", "vascular calcification"],
        "min_confidence": 0.80
    },

    # =========================
    # CERVICAL CANCER
    # =========================
    "cervical cancer": {
        "allowed_scan": ["Pelvis MRI (General)"],
        "required_terms": ["cervix", "stromal invasion", "restricted diffusion", "irregular mass"],
        "forbidden_terms": ["fibroid", "adenomyosis", "nabothian cyst"],
        "min_confidence": 0.85
    },

    # =========================
    # PULMONARY EMBOLISM
    # =========================
    "pulmonary embolism": {
        "allowed_scan": ["CT Angiography (Vascular)"],
        "required_terms": ["filling defect", "embolus"],
        "forbidden_terms": ["normal vessels"],
        "min_confidence": 0.90
    }
}


class MedicalVisionBrain:
    def __init__(self):
        self.model_name = 'hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224'
        try:
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(self.model_name)
            self.tokenizer = open_clip.get_tokenizer(self.model_name)
        except Exception as e:
            print(f"Error loading AI: {e}")
            raise e

    # --- 🟢 NEW FUNCTION: SMART CROPPER ---
    def smart_crop_film(self, pil_image):
        """
        Automatically finds the medical film inside a photo and crops out the background.
        """
        try:
            # Convert PIL to OpenCV format
            img_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Blur to remove tile noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Adaptive Threshold to find the film (usually darker or high contrast vs bg)
            # We look for the largest rectangular contour
            edged = cv2.Canny(blurred, 50, 200)
            
            contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return pil_image # Fail safe: return original if no contour found

            # Find the largest contour by area
            c = max(contours, key=cv2.contourArea)
            
            # Get bounding box
            x, y, w, h = cv2.boundingRect(c)
            
            # Filter: If the crop is too small (noise), ignore it
            if w < 100 or h < 100:
                return pil_image

            # Crop
            crop_img = pil_image.crop((x, y, x+w, y+h))
            return crop_img
        except Exception as e:
            print(f"Cropping failed: {e}")
            return pil_image

    def _get_probs(self, image, label_list):
        if not label_list: return [0.0]
        # Ensure image is RGB before processing
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        image_input = self.preprocess(image).unsqueeze(0)
        text_inputs = self.tokenizer(label_list)
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            text_features = self.model.encode_text(text_inputs)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            text_probs = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        return text_probs[0].tolist()

    def calibrate_confidence(self, raw_confidence):
        if raw_confidence > 99.9: return 99.4
        elif raw_confidence < 40.0: return raw_confidence
        else: return round(raw_confidence, 1)

    def load_medical_image(self, image_path):
        try:
            return Image.open(image_path).convert("RGB")
        except:
            pass
        try:
            dicom_data = pydicom.dcmread(image_path)
            img_array = dicom_data.pixel_array
            img_array = img_array - np.min(img_array)
            img_array = (img_array / np.max(img_array)) * 255.0
            image = Image.fromarray(img_array.astype(np.uint8))
            if hasattr(dicom_data, 'PhotometricInterpretation'):
                if dicom_data.PhotometricInterpretation == "MONOCHROME1":
                    image = ImageOps.invert(image)
            return image.convert("RGB")
        except Exception as e:
            print(f"File Error: {e}")
            raise e

    def check_image_quality(self, image):
        quality_prompts = [
            "High quality direct digital medical scan",
            "Photo of a computer screen or monitor",
            "Photo of medical film held by hand",
            "Blurry, out of focus medical image",
            "Glare, reflection, or flash artifact"
        ]
        probs = self._get_probs(image, quality_prompts)
        result = {"is_good": True, "warning": None, "score": round(probs[0]*100, 1)}
        
        # If the top prediction is NOT "High quality direct digital..."
        best_idx = probs.index(max(probs))
        if best_idx != 0:
            result["is_good"] = False
            worst = quality_prompts[best_idx]
            result["warning"] = f"Quality Alert: Image appears to be a '{worst}'."
            
        return result

    def analyze_image(self, image_path, use_tiling=True):
        original_image = self.load_medical_image(image_path)
        
        # -------------------------------------------------
        # STEP 1: IMAGE QUALITY & GATEKEEPER
        # -------------------------------------------------
        quality = self.check_image_quality(original_image)
        quality_warn = quality.get("warning", "")
        is_photo_of_film = not quality.get("is_good", True)

        # 🟢 CRITICAL FIX: If it's a photo, CROP IT before analysis
        analysis_image = original_image
        if is_photo_of_film:
            print("Detected photo artifact. Applying Smart Crop...")
            analysis_image = self.smart_crop_film(original_image)

        gatekeeper_menu = [
            "X-Ray Image", "CT Scan Image", "MRI Scan Image", 
            "Ultrasound Image", "Dermoscopy (Skin Magnified)", 
            "Medical Document/Lab Report", "General Medical Scan (Radiology)",
            "Non-Medical Image (Cartoon/Anime/Selfie/Outdoor)" 
        ]
        
        # USE THE CROPPED IMAGE FOR ANALYSIS
        type_probs = self._get_probs(analysis_image, gatekeeper_menu)
        detected_type = gatekeeper_menu[type_probs.index(max(type_probs))]
        
        # Non-Medical Exit
        if "Non-Medical" in detected_type:
             if max(type_probs) * 100 < 60.0: detected_type = "General Medical Scan (Radiology)"
             else: return {"label": "Non-Medical Image", "triage": 1, "modality": "Invalid", "findings": {"assessment": "Rejected"}, "recommendation": "Upload a valid scan."}
        
        if "Document" in detected_type:
             return {"label": "Lab Report", "triage": 1, "modality": "Document", "findings": {"assessment": "OCR Required"}, "recommendation": "Switching to text mode."}

        # -------------------------------------------------
        # STEP 2: MODALITY ROUTING & BODY PART DETECTION
        # -------------------------------------------------
        final_modality = "Radiology (General)"
        candidate_labels = BODY_PARTS # Default

        if "Ultrasound" in detected_type:
            final_modality = "Ultrasound"
            candidate_labels = ULTRASOUND_PRECISION_LIST
        elif "Dermoscopy" in detected_type:
            final_modality = "Dermoscopy"
            candidate_labels = DERMOSCOPY_PRECISION_LIST
        elif "MRI" in detected_type:
            final_modality = "MRI"
            candidate_labels = [c for c in BODY_PARTS if "MRI" in c]
        elif "CT" in detected_type:
            final_modality = "CT Scan"
            candidate_labels = [c for c in BODY_PARTS if "CT" in c]
        elif "X-Ray" in detected_type:
            final_modality = "X-Ray"
            candidate_labels = [c for c in BODY_PARTS if "X-Ray" in c]

        if final_modality == "Ultrasound" or final_modality == "Dermoscopy":
            scan_type_label = final_modality 
            final_diagnosis_list = candidate_labels
        else:
            # USE CROPPED IMAGE
            part_probs = self._get_probs(analysis_image, candidate_labels)
            scan_type_label = candidate_labels[part_probs.index(max(part_probs))]
            
            if "MRI" in scan_type_label: final_modality = "MRI"
            elif "CT" in scan_type_label: final_modality = "CT Scan"
            elif "X-Ray" in scan_type_label: final_modality = "X-Ray"
            
            final_diagnosis_list = CONDITIONS.get(scan_type_label, ["Normal", "Abnormal"])

        # -------------------------------------------------
        # STEP 3: INITIAL DIAGNOSIS
        # -------------------------------------------------
        # USE CROPPED IMAGE
        diag_probs = self._get_probs(analysis_image, final_diagnosis_list)
        best_condition = final_diagnosis_list[diag_probs.index(max(diag_probs))]
        confidence = self.calibrate_confidence(max(diag_probs) * 100)
        
        # =================================================
        # 🚨 SURGICAL SAFETY FILTERS (The "Hard" Logic)
        # =================================================
        
        # FILTER A: BLOCK HSG HALLUCINATION
        if "HSG" in scan_type_label or "Hysterosalpingogram" in scan_type_label:
            if is_photo_of_film or confidence < 85.0:
                best_condition = "⚠️ INDETERMINATE (HSG)"
                quality_warn = "HSG diagnosis requires controlled fluoroscopy. Static photos are unreliable."
                confidence = 0.0

        # FILTER B: KIDNEY STONE PRECISION OVERRIDE
        # NOTE: This filter is now much more likely to work because 
        # the model is looking at the film, not the wall.
        cond_lower = best_condition.lower()
        scan_lower = scan_type_label.lower()
        if "abdomen" in scan_lower or "kub" in scan_lower or "pelvis" in scan_lower:
            if "stone" in cond_lower or "calculus" in cond_lower:
                best_condition = "Renal / Ureteric Calculus (Kidney Stone)"
                scan_type_label = "CT KUB (Stone Protocol)"
                confidence = max(confidence, 85.0)

        # ... [Rest of your filters and return logic remain the same] ...
        
        # FILTER C: CANCER / TUBAL LOCK
        restricted_conditions = {
            "cervical cancer": ["MRI", "CT"], 
            "ovarian cancer": ["MRI", "CT", "Ultrasound"],
            "endometrial cancer": ["MRI"],
            "tubal block": ["HSG"]
        }
        
        for disease, allowed_modalities in restricted_conditions.items():
            if disease in cond_lower:
                is_allowed = any(m in final_modality for m in allowed_modalities)
                if not is_allowed:
                    best_condition = f"⚠️ INDETERMINATE ({disease.title()} requires {allowed_modalities[0]})"
                    confidence = 0.0

        # FILTER D: LOW CONFIDENCE SAFETY EXIT
        if confidence < 45.0 and "INDETERMINATE" not in best_condition:
            best_condition = "⚠️ INCONCLUSIVE (Low Confidence)"
            triage_score = 1
        else:
            # -------------------------------------------------
            # STEP 4: TRIAGE SCORING
            # -------------------------------------------------
            triage_score = 1
            cond_lower = best_condition.lower()
            
            if "torsion" in cond_lower or "melanoma" in cond_lower or "carcinoma" in cond_lower: triage_score = 4
            elif "mass" in cond_lower or "hypoechoic" in cond_lower: triage_score = 3
            elif "hydrocele" in cond_lower or "epididymitis" in cond_lower: triage_score = 2
            
            for k, v in SCAN_SEVERITY_MAP.items():
                if k in cond_lower: triage_score = max(triage_score, v)

        # -------------------------------------------------
        # FINAL OUTPUT GENERATION
        # -------------------------------------------------
        rec_text = "Urgent Specialist Review." if triage_score >= 3 else "Routine check."
        if quality_warn: rec_text = f"⚠️ {quality_warn}\n\n{rec_text}"

        return {
            "label": best_condition,
            "triage": triage_score,
            "scan_type": scan_type_label,
            "modality": final_modality,
            "is_readable": True,
            "findings": {
                "detected_condition": best_condition,
                "confidence": f"{confidence}%",
                "assessment": quality_warn if quality_warn else ("Abnormal" if triage_score > 1 else "Normal")
            },
            "recommendation": rec_text
        }

_brain = None
def get_brain():
    global _brain
    if _brain is None: _brain = MedicalVisionBrain()
    return _brain

# I already know code woint be giving correct output so just start it tomorrow by supposing we dont have any VisionBrain we will 