<script lang="ts">
    import { appState } from '../state.svelte';
</script>

{#if appState.confirmModal}
<div class="modal-overlay">
    <div class="confirm-card">
        <div class="modal-header">
            <h3>{appState.confirmModal.title}</h3>
        </div>
        <div class="modal-body">
            <p>{appState.confirmModal.message}</p>
        </div>
        <div class="modal-footer">
            <button class="cancel-btn" onclick={appState.confirmModal.onCancel}>Cancel</button>
            <button class="confirm-btn" onclick={appState.confirmModal.onConfirm}>Confirm Action</button>
        </div>
    </div>
</div>
{/if}

<style>
    .modal-overlay {
        position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(12px);
        display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 20px;
    }
    .confirm-card {
        background: #13121a; border: 1px solid rgba(42, 40, 64, 1); border-radius: 16px;
        padding: 24px; width: 100%; max-width: 340px; box-shadow: 0 40px 80px -20px rgba(0, 0, 0, 0.9);
        text-align: center;
    }
    .modal-header h3 {
        margin: 0; font-family: 'Bebas Neue', sans-serif; font-size: 22px; color: #e8e6f0; letter-spacing: 0.1em;
    }
    .modal-body p {
        font-size: 13px; color: #6b6882; line-height: 1.5; margin: 16px 0 24px;
    }
    .modal-footer { display: flex; gap: 12px; justify-content: stretch; }
    
    .cancel-btn {
        flex: 1; background: #0d0c16; border: 1px solid #1e1c2a; color: #6b6882;
        padding: 12px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.2s;
    }
    .confirm-btn {
        flex: 1; background: #f87171; color: #fff; border: none;
        padding: 12px; border-radius: 8px; font-weight: 700; cursor: pointer; transition: 0.2s;
        box-shadow: 0 4px 12px rgba(248, 113, 113, 0.3);
    }
    .confirm-btn:hover { background: #ff5e5e; transform: translateY(-1px); }
</style>
