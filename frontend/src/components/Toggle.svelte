<script lang="ts">
    interface Props {
        label: string;
        checked: boolean;
        onToggle: () => void;
    }
    let { label, checked, onToggle }: Props = $props();
</script>

<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #1a1826">
    <span style="font-size:12px;color:#a09cc0">{label}</span>
    <div 
        class="toggle {checked ? 'on' : 'off'}" 
        onclick={onToggle}
        onkeydown={(e) => e.key === 'Enter' && onToggle()}
        role="button"
        tabindex="0"
    >
        <span></span>
    </div>
</div>
