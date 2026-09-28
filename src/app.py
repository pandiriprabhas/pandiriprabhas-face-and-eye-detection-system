import cv2
import typer
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from .detector import HaarDetector
from .utils import FPSCounter, enhance_gray, draw_detections
from .video import open_source

app = typer.Typer(help="Enhanced Face & Eye Detection using Haar Cascades (Internship Project)")
console = Console()


@app.command()
def run(source: str = typer.Argument("0", help="Camera index or path to video/image"),
        record: bool = typer.Option(False, help="Record annotated output to file"),
        output: Path = typer.Option(Path("output.mp4"), help="Recording output path"),
        scale_factor: float = typer.Option(1.1, help="Haar scale factor"),
        min_neighbors: int = typer.Option(5, help="Haar min neighbors"),
        width: int = typer.Option(0, help="Optional resize width"),
        backend: str = typer.Option("auto", help="Capture backend: auto|avfoundation|qt|any|v4l2"),
        capture_dir: Path = typer.Option(Path("data/captures"), help="Directory to save snapshots when pressing space")):
    """Run real-time detection."""
    try:
        cap = open_source(source, backend)
    except Exception as e:
        console.print(f"[red]Error opening source: {e}")
        raise typer.Exit(code=1)

    detector = HaarDetector(scale_factor=scale_factor, min_neighbors=min_neighbors)
    fpsc = FPSCounter()
    writer = None

    # prepare capture directory (space bar)
    save_dir = Path(capture_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            console.print("[yellow]End of stream or read failure.")
            break
        if width > 0:
            frame = cv2.resize(frame, (width, int(frame.shape[0]*width/frame.shape[1])))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = enhance_gray(gray)
        faces, eyes = detector.detect(gray)
        annotated = draw_detections(frame.copy(), faces, eyes)
        fps = fpsc.update()
        cv2.putText(annotated, f"Faces: {len(faces)} Eyes: {len(eyes)} FPS: {fps:.1f}", (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

        cv2.imshow("Enhanced Face & Eye Detection", annotated)
        if record:
            if writer is None:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(output), fourcc, 20.0, (annotated.shape[1], annotated.shape[0]))
            writer.write(annotated)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            # snapshot on space bar
            fname = save_dir / f"capture_{cv2.getTickCount()}.png"
            cv2.imwrite(str(fname), annotated)
            console.print(f"[green]Saved snapshot: {fname}")
        if key in (27, ord('q')):
            break

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

@app.command()
def gui(source: str = typer.Argument("0", help="Camera index or path to video"),
        backend: str = typer.Option("auto", help="Capture backend: auto|avfoundation|qt|any|v4l2"),
        scale_factor: float = typer.Option(1.1, help="Haar scale factor"),
        min_neighbors: int = typer.Option(5, help="Haar min neighbors"),
        width: int = typer.Option(0, help="Optional resize width")):
    """Launch a simple GUI with Capture and Quit buttons."""
    try:
        from .gui import launch_gui  # local import avoids circular dependency
        launch_gui(source, backend, scale_factor, min_neighbors, width)
    except Exception as e:
        console.print(f"[red]GUI error: {e}")
        raise typer.Exit(code=1)

@app.command()
def benchmark(frames: int = 200, width: int = 640):
    """Benchmark detection FPS on a dummy camera feed."""
    cap = open_source(0)
    detector = HaarDetector()
    fpsc = FPSCounter()
    processed = 0
    while processed < frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (width, int(frame.shape[0]*width/frame.shape[1])))
        gray = enhance_gray(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        detector.detect(gray)
        fps = fpsc.update()
        processed += 1
    cap.release()
    table = Table(title="Benchmark")
    table.add_column("Frames")
    table.add_column("Approx FPS")
    table.add_row(str(frames), f"{fpsc.fps:.1f}")
    console.print(table)

@app.command()
def cameras(backend: str = typer.Option("auto", help="Backend: auto|avfoundation|qt|any|v4l2"),
            max_index: int = typer.Option(5, help="Probe camera indices 0..max_index")):
    """List available camera indices and basic info."""
    from rich import box
    table = Table(title="Camera Probe", box=box.SIMPLE)
    table.add_column("Index")
    table.add_column("Status")
    table.add_column("Resolution")
    for i in range(max_index + 1):
        try:
            cap = open_source(i, backend)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                table.add_row(str(i), "available", f"{w}x{h}")
                cap.release()
            else:
                table.add_row(str(i), "unavailable", "-")
        except Exception as e:
            table.add_row(str(i), f"unavailable ({str(e).split('.')[0]})", "-")
    console.print(table)

if __name__ == "__main__":
    app()
