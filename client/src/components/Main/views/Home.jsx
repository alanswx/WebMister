import React from 'react';
import { Grid } from 'semantic-ui-react';
import PlatformMenu from '../../PlatformMenu/PlatformMenu.jsx';
import Platform from '../../Platform/Platform.jsx';

class Home extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      platform: null
    };

    this.onPlatformChange = this.onPlatformChange.bind(this);
  }

  onPlatformChange(platform) {

    const { repo, releaseDir } = platform;
    const url = `https://api.github.com/repos/${repo}/contents/${releaseDir}`;

    window.fetch(url)
      .then(response => response.text())
      .then((releases) => {
        this.setState({
          platform,
          releases: releases ? JSON.parse(releases) : null
        });
      });
  }


  render() {
    const { platform, releases } = this.state;

    return (
      <Grid>
        <Grid.Column width={4}>
          <PlatformMenu onPlatformChange={this.onPlatformChange} platform={platform} />
        </Grid.Column>
        <Grid.Column width={12}>
          <Platform platform={platform} releases={releases} />
        </Grid.Column>
      </Grid>
    );
  }
}

export default Home;
