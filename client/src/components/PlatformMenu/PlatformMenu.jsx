import 'whatwg-fetch';
import React from 'react';
import PropTypes from 'prop-types';
import {  Input, Menu, Image } from 'semantic-ui-react';

class PlatformMenu extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selected: null,
      manifest: null,
      searchText: null
    };
    this.search = this.search.bind(this);
    this.handleItemClick = this.handleItemClick.bind(this);
  }

  componentWillMount() {
    window.fetch('/api/load_manifest')
      .then(response => response.text())
      .then((manifest) => {
        const json = JSON.parse(manifest);
        this.setState({
          manifest: json
        });
      });
  }

  search(e, { value }) {
    this.setState({
      searchText: value.length ? value.toLowerCase() : null
    });
  }

  handleItemClick(e, { name }) {
    const { onPlatformChange } = this.props;

    this.setState({
      selected: name
    });

    const { manifest } = this.state;
    onPlatformChange(manifest[name]);
  }

  render() {
    const { selected, manifest, searchText } = this.state;
    const platformList = manifest ? Object.keys(manifest).map((platformName) => {
      const { name } = manifest[platformName];
      manifest[platformName].platformName=platformName;
      let imsrc ='';
      if (manifest[platformName] && manifest[platformName].type)
      {
           if (manifest[platformName].type==='arcade')
           {
              imsrc =  '/static/images/HakchiMister/arcade/'+platformName+'.png';
           }
           else
           {
              imsrc = '/static/images/HakchiMister/'+platformName+'.png' ;
           }
      }

      if (searchText && name && name.toLowerCase().includes(searchText) === false) {
        return null;
      }

      return (
        <Menu.Item key={platformName} name={platformName} active={selected === platformName} onClick={this.handleItemClick}>
          { imsrc ? <Image src={imsrc} size="tiny" verticalAlign="middle" /> : '' } <span>{ name }</span>
        </Menu.Item>
      );
    }) : null;

    return (
      <Menu vertical fluid >
        <Menu.Item>
          <Input placeholder="Search..." onChange={this.search} />
        </Menu.Item>
        <Menu.Item>
          Platforms
          <Menu.Menu>
            { platformList }
          </Menu.Menu>
        </Menu.Item>

      </Menu>
    );
  }
}

PlatformMenu.propTypes = {
  onPlatformChange: PropTypes.func.isRequired
};

export default PlatformMenu;
