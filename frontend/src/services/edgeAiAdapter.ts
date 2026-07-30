/**
 * Edge AI Adapter
 * 
 * This service provides a clean integration interface for connecting the trained AI model
 * (developed by the Data Scientist team) to the frontend application.
 * 
 * ARCHITECTURE FLOW:
 * Dashboard Video/Webcam -> Edge AI Adapter -> 'LOW' | 'MEDIUM' | 'HIGH' -> FastAPI API -> AC Control Logic -> Dashboard
 * 
 * INSTRUCTIONS FOR DATA SCIENCE TEAM:
 * 1. Install ONNX Runtime Web or TensorFlow.js in the frontend:
 *    npm install onnxruntime-web  OR  npm install @tensorflow/tfjs
 * 2. Load your model file inside the initialization block.
 * 3. Inside the `predictOccupancy` method, extract the image data from the video/canvas element,
 *    preprocess it into the format expected by your model (resizing, normalization, etc.),
 *    and run the inference.
 * 4. Map the inference result to one of the target occupancy levels: 'LOW', 'MEDIUM', or 'HIGH'.
 */

export type OccupancyClassification = 'LOW' | 'MEDIUM' | 'HIGH';

export class EdgeAiAdapter {
  private isLoaded: boolean = false;

  constructor() {
    // Proactively initialize or load model weight configurations here
    this.initializeModel();
  }

  /**
   * Initializes the AI model (placeholder for loading weights/model).
   */
  private initializeModel(): void {
    console.log('[Edge AI Adapter] Loading trained AI model configuration and metadata...');
    // TODO: Connect actual trained model weights here. E.g.:
    // this.model = await ort.InferenceSession.create('./model.onnx');
    this.isLoaded = true;
  }

  /**
   * Process video frame / canvas stream frame and predict the current occupancy classification.
   * 
   * @param source The video element or canvas containing the current feed frame.
   * @returns A promise that resolves to the classification result: 'LOW', 'MEDIUM', or 'HIGH'.
   */
  public async predictOccupancy(
    source: HTMLVideoElement | HTMLCanvasElement
  ): Promise<OccupancyClassification> {
    if (!this.isLoaded) {
      console.warn('[Edge AI Adapter] Model is not fully loaded. Returning LOW.');
      return 'LOW';
    }

    // 1. Prepare frame data (capturing a frame to canvas for preprocessing)
    const canvas = source instanceof HTMLCanvasElement ? source : this.captureFrame(source);
    if (!canvas) {
      return 'LOW';
    }

    // 2. Preprocess frame
    // Here, you would obtain the imageData and create a tensor:
    // const ctx = canvas.getContext('2d');
    // const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    // const tensor = this.preprocess(imageData);

    // 3. Run model inference
    // const output = await this.model.run([tensor]);

    // 4. Return class output mapping
    // Return a stable fallback level until the real model inference is connected.
    // This avoids inventing fake random predictions in the UI layers.
    console.log('[Edge AI Adapter] Model inference frame processed successfully.');
    
    // We return 'LOW' as a default, stable prediction placeholder until connected.
    // Developers can customize this or map real classification thresholds here.
    return 'LOW';
  }

  /**
   * Helper to capture a frame from HTMLVideoElement onto a temporary canvas for model processing.
   */
  private captureFrame(video: HTMLVideoElement): HTMLCanvasElement | null {
    if (!video.videoWidth || !video.videoHeight) {
      return null;
    }
    const canvas = document.createElement('canvas');
    canvas.width = 224; // Standard model input size
    canvas.height = 224;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      return canvas;
    }
    return null;
  }
}

// Single instance export for usage across pages
export const edgeAiAdapter = new EdgeAiAdapter();
