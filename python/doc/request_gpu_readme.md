## Requesting GPU Quota Increase in Google Cloud

If you encounter the error:
Quota 'GPUS_ALL_REGIONS' exceeded. Limit: 0.0 globally.
…it means your project doesn't currently have any GPU quota, and you need to request an increase.

---

### Step-by-step Instructions

1. **Open the Quotas page:**  
   👉 [https://console.cloud.google.com/iam-admin/quotas](https://console.cloud.google.com/iam-admin/quotas)

2. **Filter by GPU quota:**  
   In the **Filter** box at the top, type: 
>GPU

Look for:
- `GPUS (all regions)`

3. **Select the relevant quotas:**  
Check the box next to the quotas you'd like to increase.

4. **Click “Edit Quotas”**  
A side panel will open with a form.

5. **Fill in the form:**
- **New limit**: e.g., `1`
- **Justification**:

  ```
  We are using a VM with NVIDIA T4 GPU for machine learning model inference and experimentation. We need access to 1 GPU for development and testing purposes.
  ```
- **Email**: your contact email **(Required)**
- **Phone number**: your phone (Not required)

6. **Submit the request**  
Google will typically respond within 24–48 hours.

---

### 💡 Tips

- Consider **preemptible GPUs** if you only need them temporarily.
- Make sure **Billing is enabled** for your project.
- You can request **multiple quotas** in the same form (different regions or GPU types).


