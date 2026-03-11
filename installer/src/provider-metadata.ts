import metadata from '../../shared/provider-metadata.json' with { type: 'json' };

export type InstallerProviderMetadata = {
  name: string;
  aliases: string[];
  config_keys: string[];
  supports_self_hosted: boolean;
  installer: {
    label: string;
    hint: string;
  };
};

export function getInstallerProviders(): InstallerProviderMetadata[] {
  return metadata.providers as InstallerProviderMetadata[];
}
