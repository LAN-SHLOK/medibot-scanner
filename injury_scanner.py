import torch
import open_clip
from PIL import Image
import io

# Force CPU if CUDA is causing issues, otherwise use auto
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class InjuryScanner:
    def __init__(self):
        print("⚡ Initializing Medical Vision Brain...")
        
        # 1. Load BioMedCLIP (Vision Model)
        try:
            # Load Model and Preprocessing transform
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                'hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224'
            )
            
            # Load Tokenizer (In OpenCLIP, this is a callable function, not an object)
            self.tokenizer = open_clip.get_tokenizer('hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224')
            
            self.model.to(DEVICE)
            print("✅ AI Models Loaded Successfully")
            
        except Exception as e:
            print(f"❌ Model Loading Failed: {e}")
            raise e

        self.knowledge_base = {}

    def ingest_knowledge(self, knowledge_dict):
        """
        Loads the medical JSON knowledge into memory
        """
        self.knowledge_base = knowledge_dict
        count = sum(len(v) for v in knowledge_dict.values())
        print(f"🧠 Knowledge Ingested: {count} scan types known.")

    def analyze_image(self, image_bytes):
        """
        Main function to classify the image
        """
        try:
            # 1. Preprocess Image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            image_input = self.preprocess(image).unsqueeze(0).to(DEVICE)

            # 2. Prepare Labels from Knowledge Base
            all_labels = []
            label_map = {} 

            index = 0
            for category, sub_dict in self.knowledge_base.items():
                for condition, details in sub_dict.items():
                    desc = details.get("visuals", condition)
                    
                    # Truncate to avoid token limits
                    if len(desc) > 77: desc = desc[:77]
                    
                    all_labels.append(desc)
                    label_map[index] = {
                        "category": category,
                        "condition": condition,
                        "details": details
                    }
                    index += 1
            
            # Add Control Label
            all_labels.append("healthy normal medical scan")
            label_map[index] = {"category": "Normal", "condition": "Healthy", "details": {"severity": 0, "summary": "No abnormalities detected."}}

            # 3. Run Inference
            with torch.no_grad():
                # --- THE FIX IS HERE ---
                # We call the tokenizer directly as a function
                text_tokens = self.tokenizer(all_labels).to(DEVICE)
                
                # Encode Image & Text
                image_features = self.model.encode_image(image_input)
                text_features = self.model.encode_text(text_tokens)

                # Normalize and Compare
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)

                text_probs = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                
                # Get Top Prediction
                top_probs, top_labels = text_probs.cpu().topk(1)
                idx = top_labels[0].item()
                confidence = top_probs[0].item()

            # 4. Return Result
            result_data = label_map.get(idx)
            
            return {
                "verdict": result_data["condition"],
                "category": result_data["category"],
                "severity_score": result_data["details"].get("severity", 1),
                "summary": result_data["details"].get("summary", "Analysis complete."),
                "confidence": f"{confidence:.2f}%"
            }

        except Exception as e:
            print(f"❌ Analysis Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "verdict": "Scan Error",
                "summary": "Could not analyze image.",
                "severity_score": 0
            }