import dspy
import logging
from typing import Literal, List
from PIL import Image
from config import AppConfig


logger = logging.getLogger(__name__)


####################################################################
#                            Signatures                            #
####################################################################

class DocTextAnalysis(dspy.Signature):
    """Analyze extracted PDF text content."""
    text: str = dspy.InputField(
        desc="Unstructured text extracted from the PDF. May contain ordering or readability issues."
    )
    text_quality: Literal["good", "poor", "unusable"] = dspy.OutputField(
        desc="Assessment of the extracted text quality"
    )
    description: str = dspy.OutputField(
        desc="One-sentence description of the document's purpose."
    )
    summary: str = dspy.OutputField(
        desc="Brief 3-5 sentence summary of the document content."
    )
    notable_info: List[str] = dspy.OutputField(
        desc="Bullet list of notable items (e.g., timestamps, author, issuer). Format: ['EntityType: Value']. Should not duplicate the summary. Empty if none."
    )

class DocImagesAnalysis(dspy.Signature):
    """Analyze scanned PDF pages"""
    images: List[dspy.Image] = dspy.InputField(
        desc="Scanned document pages as images."
    )
    description: str = dspy.OutputField(
        desc="One-sentence description of the document's purpose."
    )
    summary: str = dspy.OutputField(
        desc="Brief 3-5 sentence summary of the document content."
    )
    notable_info: List[str] = dspy.OutputField(
        desc="Bullet list of notable items (e.g., timestamps, author, issuer). Format: ['Key: Value']. Should not duplicate the summary. Empty if none."
    )

class DocAnalysisCombined(dspy.Signature):
    """Combines textual and visual analysis results from a PDF."""
    results_from_text: dict = dspy.InputField(
        desc="Analysis results from the text-based extraction."
    )
    results_from_images: dict = dspy.InputField(
        desc="Analysis results from the image-based extraction."
    )
    description: str = dspy.OutputField(
        desc="One-sentence description of the document's overall purpose, combining text and image cues."
    )
    summary: str = dspy.OutputField(
        desc="Comprehensive 3-5 sentence summary that integrates findings from both text and visual analysis."
    )
    notable_info: List[str] = dspy.OutputField(
        desc="Consolidated list of notable details. Format: ['Key: Value']. Empty if none."
    )

class AnalysisValidation(dspy.Signature):
    """Ensures combined analysis reliability"""
    text: str = dspy.InputField(
        desc="Unstructured text extracted from the PDF. May contain ordering or readability issues."
    )
    images: List[dspy.Image] = dspy.InputField(
        desc="Scanned PDF document pages as images."
    )
    analysis_results: dict = dspy.InputField(
        desc="Description, summary and notable information of the PDF; analyzed from the text and images inputs."
    )
    confidence_score: float = dspy.OutputField(
        desc="0-1 score reflecting analysis reliability"
    )
    validation_notes: List[str] = dspy.OutputField(
        desc="Specific issues found"
    )

####################################################################
#                          Analyzer Module                         #
####################################################################

class DocumentAnalyzer(dspy.Module):
    """
    Performs multi-modal analysis on PDF content.
    
    The analyzer first processes text and image inputs using separate DSPy modules
    and then fuses the results.If the text extraction quality is determined to be 
    'unusable', only image analysis results are used.
    """

    def __init__(self):
        super().__init__()
        self.analyze_text = dspy.ChainOfThought(DocTextAnalysis)
        self.analyze_images = dspy.ChainOfThought(DocImagesAnalysis)
        self.combine = dspy.ChainOfThought(DocAnalysisCombined)
        self.validate = dspy.ChainOfThought(AnalysisValidation)

    def forward(self, text: str, images: List[Image.Image]):
        text_results = self._analyze_text(text)
        images_results = self._analyze_images(images)

        combined_results = self._combine_results(text_results, images_results)
        validation_results = self._validate_results(text, images, combined_results)

        if validation_results.confidence_score < AppConfig.MIN_CONFIDENCE:
            logger.warning(f"Confidence score {validation_results.confidence_score} lower than threshhold {AppConfig.MIN_CONFIDENCE}")

        return self._format_output(
            combined_results,
            validation_results
        )
    
    def _analyze_text(self, text: str):
        try:
            logger.info("Starting analysis from text modality...")
            result = self.analyze_text(text=text)
            return result
        except Exception as e:
            logger.error(f"Text analysis failed: {e}", exc_info=True)
            return dspy.Prediction(
                description="unknown",
                summary="Text analysis unavailable",
                notable_info=[],
                text_quality="unusable"
            )

    def _analyze_images(self, images: List[Image.Image]):
        try:
            logger.info("Starting analysis from image modality...")
            dspy_images = [dspy.Image.from_PIL(img) for img in images]
            result = self.analyze_images(images=dspy_images)
            return result
        except Exception as e:
            logger.error(f"Image analysis failed: {e}", exc_info=True)
            return dspy.Prediction(
                description="unknown",
                summary="Text analysis unavailable",
                notable_info=[]
            )
        
    def _combine_results(self, r_text: dspy.Prediction, r_images: dspy.Prediction):
        try:
            logger.info("Combining analysis results...")
            if r_text.text_quality == "unusable": # If text quality is unusable, use only image-based results.
                logger.warning("Extracted text unsusable, only using visual analysis results.")
                combined_results = r_images
            else: # Otherwise, fuse the results
                combined_results = self.combine(
                    results_from_text={
                        "text_quality": r_text.text_quality,
                        "description": r_text.description, 
                        "summary": r_text.summary, 
                        "notable_info": r_text.notable_info
                    }, 
                    results_from_images={
                        "description": r_images.description, 
                        "summary": r_images.summary, 
                        "notable_info": r_images.notable_info
                    }
                )
            return combined_results
        except Exception as e:
            logger.error("Combining analysis results failed: {e}", exc_info=True)
            return dspy.Prediction(
                description="unknown",
                summary="Text analysis unavailable",
                notable_info=[]
            )
        
    def _validate_results(self, text: str, images: List[Image.Image], r_combined: dspy.Prediction):
        try:
            results = {
                "description": r_combined.description, 
                "summary": r_combined.summary, 
                "notable_info": r_combined.notable_info
            }
            validation_results = self.validate(
                text=text, 
                images=images,
                analysis_results=results
            )
            return validation_results
        except Exception as e:
            logger.warning("Results validation failed: {e}", exc_info=True)
            return dspy.Prediction(
                confidence_score=0.0,
                validation_notes=[]
            )
    
    def _format_output(self, r_combined: dspy.Prediction, r_validation: dspy.Prediction):
        return {
            "description": r_combined.description, 
            "summary": r_combined.summary, 
            "notable_info": r_combined.notable_info,
            "confidence": {
                "score": r_validation.confidence_score,
                "notes": r_validation.validation_notes
            },
        }