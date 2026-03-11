/**
 * Future prompt contract for provider selection.
 *
 * The real implementation should present checkbox-style provider selection
 * using metadata from the runtime provider registry.
 */

export type ProviderSelection = {
  selectedProviders: string[];
};
