# Batch Bake Addon (Blender 5.x)

Batch Bake Addon is a Blender tool that automates high-to-low texture baking using cage meshes. It is designed to speed up repetitive baking workflows by processing multiple objects and channels in a single operation.

---

## ✨ Features

* Batch bake multiple objects automatically
* Collection-based workflow (Low / High / Cage)
* Name-based object matching (`.low`, `.high`, `.cage`)
* Multiple bake channels:

  * Diffuse
  * Metallic *(approximate)*
  * Specular Tint *(approximate)*
  * Roughness
  * Emission
  * Sheen Tint *(approximate)*
  * Normal
  * Height *(approximate)*
* Custom resolution and output format (PNG, TIFF, OpenEXR)
* Adjustable bake margin
* Automatic image creation and saving
* Progress feedback during baking

---

## 📦 Installation

1. Download the addon `.py` file
2. Open Blender
3. Go to **Edit > Preferences > Add-ons**
4. Click **Install** and select the file
5. Enable **Batch Bake Addon**

---

## 🚀 Usage

1. Organize your scene into three collections:

   * **Low-poly collection**
   * **High-poly collection**
   * **Cage collection**

2. Name your objects consistently:
   object.low
   object.high
   object.cage

3. Open:
   **Render Properties > Batch Bake**

4. Configure:

   * Output path
   * Resolution
   * Bake channels

5. Click **Start Baking**

---

## ⚠️ Notes

* Some channels use approximations due to Blender limitations
* Each low-poly object must have a material assigned
* Object naming must match for automatic pairing

---

## 🎯 Use Cases

* Game asset pipelines
* Environment production
* Bulk texture baking
* Workflow automation

---

## 👤 Author

**Pietro3DArtist**

---

## 📄 License

GPLv3

